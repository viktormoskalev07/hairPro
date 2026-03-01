import { NextRequest, NextResponse } from 'next/server';

export const maxDuration = 60;

export async function POST(req: NextRequest) {
  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) {
    return NextResponse.json({ error: 'API key not configured' }, { status: 500 });
  }

  const { photoBase64, wigBase64, customPrompt } = await req.json();

  if (!photoBase64) {
    return NextResponse.json({ error: 'No photo provided' }, { status: 400 });
  }

  // Build the prompt
  let prompt = customPrompt?.trim() || '';

  if (!prompt) {
    if (wigBase64) {
      prompt = `You are a professional hair stylist and photo editor.
Apply the hairstyle from the SECOND image naturally onto the person in the FIRST image.
Make it look completely photorealistic:
- Match the lighting, shadows and highlights of the original photo
- Blend the hair naturally with the person's head shape and skin tone
- Keep the person's face, expression, eyes and background completely unchanged
- The result should look like a real professional photo, not a composite
Output only the final image with no text.`;
    } else {
      prompt = 'Enhance this portrait photo professionally. Improve lighting, colors and overall quality while keeping the person looking natural.';
    }
  } else if (wigBase64) {
    prompt += '\nUse the hairstyle from the second image as reference.';
  }

  // Build contents array
  const parts: object[] = [
    { text: prompt },
    {
      inline_data: {
        mime_type: 'image/jpeg',
        data: photoBase64,
      },
    },
  ];

  if (wigBase64) {
    parts.push({
      inline_data: {
        mime_type: 'image/png',
        data: wigBase64,
      },
    });
  }

  const body = {
    contents: [{ role: 'user', parts }],
    generationConfig: {
      responseModalities: ['IMAGE', 'TEXT'],
      responseMimeType: 'image/jpeg',
    },
  };

  const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp-image-generation:generateContent?key=${apiKey}`;

  const geminiRes = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  if (!geminiRes.ok) {
    const err = await geminiRes.text();
    console.error('Gemini error:', err);
    return NextResponse.json({ error: `Gemini API error: ${geminiRes.status}` }, { status: 502 });
  }

  const data = await geminiRes.json();

  // Extract the image from the response
  const candidates = data?.candidates ?? [];
  for (const candidate of candidates) {
    for (const part of candidate?.content?.parts ?? []) {
      if (part.inline_data?.data) {
        return NextResponse.json({
          imageBase64: part.inline_data.data,
          mimeType: part.inline_data.mime_type ?? 'image/jpeg',
        });
      }
    }
  }

  // If no image returned, check for text (error message from model)
  const textPart = candidates[0]?.content?.parts?.find((p: { text?: string }) => p.text);
  return NextResponse.json(
    { error: textPart?.text ?? 'No image in response' },
    { status: 502 }
  );
}
