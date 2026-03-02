'use client';

import React, { useState, useRef, useEffect, useCallback } from 'react';
import wigsData from './wigs_data.json';

type Wig = {
  id: string;
  src: string;
  name: string;
  category?: string;
};

type Category = { id: string; label: string };

const AVAILABLE_WIGS: Wig[] = wigsData;

const ALL_CATEGORIES: Category[] = [
  { id: 'all',                label: 'Все' },
  { id: 'women-classic',      label: 'Женские · Классика' },
  { id: 'women-long',         label: 'Женские · Длинные' },
  { id: 'women-curly',        label: 'Женские · Кудри' },
  { id: 'women-short',        label: 'Женские · Короткие' },
  { id: 'women-updo',         label: 'Женские · Updo' },
  { id: 'women-colored',      label: 'Женские · Цветные' },
  { id: 'men-classic',        label: 'Мужские · Классика' },
  { id: 'men-fade',           label: 'Мужские · Фейды' },
  { id: 'men-textured',       label: 'Мужские · Текстурные' },
  { id: 'men-long',           label: 'Мужские · Длинные' },
  { id: 'unisex-natural',     label: 'Унисекс · Натуральные' },
  { id: 'unisex-alternative', label: 'Унисекс · Альтернатива' },
];

// Only show categories that actually have wigs
const usedCatIds = new Set(AVAILABLE_WIGS.map(w => w.category));
const CATEGORIES = ALL_CATEGORIES.filter(c => c.id === 'all' || usedCatIds.has(c.id));

export default function WigEditor() {
  const [userImage, setUserImage] = useState<string | null>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [selectedWig, setSelectedWig] = useState<Wig | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  
  const [wigTransform, setWigTransform] = useState({ x: 0, y: 0, scale: 1, rotate: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  const [isResizing, setIsResizing] = useState(false);
  const [resizeStart, setResizeStart] = useState({ scale: 1, dist: 0 });
  const [faceDetected, setFaceDetected] = useState(false);
  const [cameraReady, setCameraReady] = useState(false);

  const [aiPrompt, setAiPrompt] = useState('');
  const [aiLoading, setAiLoading] = useState(false);
  const [aiResult, setAiResult] = useState<string | null>(null);

  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const wigRef = useRef<HTMLDivElement>(null);

  const startCamera = async () => {
    try {
      setCameraReady(false);
      const mediaStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' } });
      setStream(mediaStream);
      // srcObject устанавливается в useEffect после рендера <video>
    } catch (err) {
      console.error("Error accessing camera: ", err);
      alert("Не удалось получить доступ к камере. Проверьте разрешения.");
    }
  };

  // Подключаем поток к <video> после того как элемент появился в DOM
  useEffect(() => {
    if (stream && videoRef.current) {
      videoRef.current.srcObject = stream;
      videoRef.current.play().catch(() => {});
    }
  }, [stream]);

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      setStream(null);
      setCameraReady(false);
    }
  };

  const takePhoto = () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas) return;

    // Ждём пока видео реально готово (readyState >= 2 = HAVE_CURRENT_DATA)
    if (video.readyState < 2 || video.videoWidth === 0) {
      alert('Камера ещё инициализируется, подождите секунду.');
      return;
    }

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    if (ctx) {
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      setUserImage(canvas.toDataURL('image/jpeg', 0.95));
      stopCamera();
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        setUserImage(event.target?.result as string);
        stopCamera();
      };
      reader.readAsDataURL(file);
    }
  };

  // Tries browser FaceDetector API, falls back to top-of-image heuristic
  const getDefaultWigTransform = useCallback(async () => {
    const container = containerRef.current;
    if (!container) return { x: 0, y: 0, scale: 1.5, rotate: 0 };

    const containerH = container.clientHeight;
    const containerW = container.clientWidth;

    // Try FaceDetector (Chrome/Android)
    if ('FaceDetector' in window && userImage) {
      try {
        // @ts-ignore
        const detector = new window.FaceDetector({ fastMode: true });
        const img = new Image();
        img.src = userImage;
        await new Promise(r => { img.onload = r; });
        // @ts-ignore
        const faces = await detector.detect(img);
        if (faces.length > 0) {
          const face = faces[0].boundingBox;
          // Face bounding box is relative to the original image size
          const scaleX = containerW / img.naturalWidth;
          const scaleY = containerH / img.naturalHeight;
          // Center of face in container coords
          const faceCenterX = (face.x + face.width / 2) * scaleX;
          const faceTopY = face.y * scaleY;
          // Wig should be centered horizontally on face, top aligned above face
          const wigScale = (face.width * scaleX) / 200 * 1.6; // 200px is wig base size
          const offsetX = faceCenterX - containerW / 2;
          const offsetY = (faceTopY - containerH / 2) - (face.height * scaleY * 0.15);
          setFaceDetected(true);
          return { x: offsetX, y: offsetY, scale: Math.max(0.8, Math.min(wigScale, 4)), rotate: 0 };
        }
      } catch {}
    }

    // Fallback: move wig up by ~22% of container height (portrait heuristic)
    const offsetY = -(containerH * 0.22);
    return { x: 0, y: offsetY, scale: 1.5, rotate: 0 };
  }, [userImage]);

  const reset = () => {
    setUserImage(null);
    setSelectedWig(null);
    setWigTransform({ x: 0, y: 0, scale: 1, rotate: 0 });
  };

  const getClientPos = (e: React.MouseEvent | React.TouchEvent | MouseEvent | TouchEvent) => {
    if ('touches' in e) {
      return { x: e.touches[0].clientX, y: e.touches[0].clientY };
    }
    return { x: (e as MouseEvent).clientX, y: (e as MouseEvent).clientY };
  };

  const handleMouseDown = (e: React.MouseEvent | React.TouchEvent) => {
    if (!selectedWig || isResizing) return;
    e.preventDefault();
    setIsDragging(true);
    const { x, y } = getClientPos(e);
    setDragStart({ x: x - wigTransform.x, y: y - wigTransform.y });
  };

  const handleResizeMouseDown = (e: React.MouseEvent | React.TouchEvent) => {
    e.stopPropagation();
    e.preventDefault();
    setIsResizing(true);
    const { x, y } = getClientPos(e);
    if (wigRef.current) {
      const rect = wigRef.current.getBoundingClientRect();
      const centerX = rect.left + rect.width / 2;
      const centerY = rect.top + rect.height / 2;
      const dist = Math.hypot(x - centerX, y - centerY);
      setResizeStart({ scale: wigTransform.scale, dist });
    }
  };

  const handleMouseMove = useCallback((e: MouseEvent | TouchEvent) => {
    if (isDragging) {
      const { x, y } = getClientPos(e);
      setWigTransform(prev => ({
        ...prev,
        x: x - dragStart.x,
        y: y - dragStart.y
      }));
    } else if (isResizing && wigRef.current) {
      const { x, y } = getClientPos(e);
      const rect = wigRef.current.getBoundingClientRect();
      const centerX = rect.left + rect.width / 2;
      const centerY = rect.top + rect.height / 2;
      const currentDist = Math.hypot(x - centerX, y - centerY);
      const scaleRatio = currentDist / (resizeStart.dist || 1);
      
      setWigTransform(prev => ({
        ...prev,
        scale: Math.max(0.2, Math.min(resizeStart.scale * scaleRatio, 5))
      }));
    }
  }, [isDragging, isResizing, dragStart, resizeStart]);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
    setIsResizing(false);
  }, []);

  const handleWheel = (e: React.WheelEvent) => {
    if (!selectedWig) return;
    e.preventDefault();
    const scaleAmount = -e.deltaY * 0.005;
    setWigTransform(prev => ({
      ...prev,
      scale: Math.max(0.2, Math.min(prev.scale + scaleAmount, 5))
    }));
  };

  useEffect(() => {
    if (isDragging || isResizing) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
      window.addEventListener('touchmove', handleMouseMove, { passive: false });
      window.addEventListener('touchend', handleMouseUp);
    } else {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
      window.removeEventListener('touchmove', handleMouseMove);
      window.removeEventListener('touchend', handleMouseUp);
    }
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
      window.removeEventListener('touchmove', handleMouseMove);
      window.removeEventListener('touchend', handleMouseUp);
    };
  }, [isDragging, isResizing, handleMouseMove, handleMouseUp]);

  // Сжимает dataURL до указанного размера в байтах через canvas
  const compressImage = (dataUrl: string, maxBytes = 4 * 1024 * 1024): Promise<string> =>
    new Promise((resolve) => {
      const img = new Image();
      img.onload = () => {
        const canvas = document.createElement('canvas');
        const MAX_DIM = 1920;
        let { width, height } = img;
        if (width > MAX_DIM || height > MAX_DIM) {
          const ratio = Math.min(MAX_DIM / width, MAX_DIM / height);
          width = Math.round(width * ratio);
          height = Math.round(height * ratio);
        }
        canvas.width = width;
        canvas.height = height;
        canvas.getContext('2d')!.drawImage(img, 0, 0, width, height);

        let quality = 0.92;
        const tryEncode = () => {
          const result = canvas.toDataURL('image/jpeg', quality);
          const bytes = Math.round((result.length * 3) / 4);
          if (bytes <= maxBytes || quality <= 0.3) {
            resolve(result);
          } else {
            quality -= 0.08;
            tryEncode();
          }
        };
        tryEncode();
      };
      img.src = dataUrl;
    });

  // Загружает изображение по src и возвращает base64 без префикса data:...
  const fetchImageBase64 = (src: string): Promise<string> =>
    new Promise((resolve, reject) => {
      const img = new Image();
      img.crossOrigin = 'anonymous';
      img.onload = () => {
        const canvas = document.createElement('canvas');
        canvas.width = img.naturalWidth;
        canvas.height = img.naturalHeight;
        canvas.getContext('2d')!.drawImage(img, 0, 0);
        const dataUrl = canvas.toDataURL('image/png');
        resolve(dataUrl.split(',')[1]);
      };
      img.onerror = reject;
      img.src = src;
    });

  const handleAiImprove = async () => {
    if (!userImage) return;
    setAiLoading(true);
    setAiResult(null);
    try {
      // Сжимаем фото до < 4 МБ
      const compressed = await compressImage(userImage);
      const photoBase64 = compressed.split(',')[1];

      // Загружаем парик если выбран
      let wigBase64: string | null = null;
      if (selectedWig) {
        try { wigBase64 = await fetchImageBase64(selectedWig.src); } catch {}
      }

      const res = await fetch('/api/ai-improve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ photoBase64, wigBase64, customPrompt: aiPrompt }),
      });

      const data = await res.json();
      if (data.imageBase64) {
        setAiResult(`data:${data.mimeType ?? 'image/jpeg'};base64,${data.imageBase64}`);
      } else {
        alert(`Ошибка AI: ${data.error ?? 'Нет изображения в ответе'}`);
      }
    } catch (e) {
      alert(`Ошибка: ${e}`);
    } finally {
      setAiLoading(false);
    }
  };

  const handleExport = () => {
    if (!userImage || !containerRef.current) return;
    
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const baseImg = new Image();
    baseImg.src = userImage;
    baseImg.onload = () => {
      canvas.width = baseImg.width;
      canvas.height = baseImg.height;
      ctx.drawImage(baseImg, 0, 0);

      if (selectedWig) {
        const wigImg = new Image();
        wigImg.src = selectedWig.src;
        wigImg.onload = () => {
          const rect = containerRef.current!.getBoundingClientRect();
          const scaleRatioX = baseImg.width / rect.width;
          const scaleRatioY = baseImg.height / rect.height;

          ctx.save();
          ctx.translate(
            baseImg.width / 2 + wigTransform.x * scaleRatioX,
            baseImg.height / 2 + wigTransform.y * scaleRatioY
          );
          ctx.rotate((wigTransform.rotate * Math.PI) / 180);
          ctx.scale(wigTransform.scale * scaleRatioX, wigTransform.scale * scaleRatioY);
          
          ctx.drawImage(wigImg, -100, -100, 200, 200);
          ctx.restore();

          const link = document.createElement('a');
          link.download = 'premium-hairstyle.png';
          link.href = canvas.toDataURL('image/png');
          link.click();
        };
      } else {
         const link = document.createElement('a');
         link.download = 'my-photo.png';
         link.href = canvas.toDataURL('image/png');
         link.click();
      }
    };
  };

  return (
    <div className="w-full min-h-screen bg-neutral-900 text-white font-sans selection:bg-indigo-500/30">
      <header className="w-full px-6 py-4 border-b border-neutral-800 flex items-center justify-between sticky top-0 bg-neutral-900/80 backdrop-blur z-50">
        <h1 className="text-2xl font-bold tracking-tight bg-gradient-to-r from-indigo-400 to-cyan-400 bg-clip-text text-transparent">HairStudio Pro</h1>
        <div className="text-sm font-medium text-neutral-400">Виртуальная примерка причёсок</div>
      </header>

      <main className="max-w-7xl mx-auto p-4 md:p-6">
        <div className="flex flex-col lg:flex-row gap-6 items-start">

          {/* ── Левая колонка: редактор / загрузка ── */}
          <div className="flex-1 flex flex-col gap-4 w-full">

            {/* Область фото / камеры */}
            <div
              ref={containerRef}
              className="relative w-full rounded-3xl overflow-hidden bg-neutral-800 shadow-2xl border border-neutral-700/50 select-none"
              style={{ minHeight: '480px' }}
              onWheel={handleWheel}
            >
              {userImage ? (
                <>
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={userImage} alt="Фото" className="w-full h-auto object-cover pointer-events-none" />

                  {faceDetected && (
                    <div className="absolute top-3 left-3 flex items-center gap-1.5 px-3 py-1.5 bg-green-500/20 border border-green-500/40 rounded-full text-green-400 text-xs font-semibold backdrop-blur pointer-events-none">
                      <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
                      Лицо определено — причёска позиционирована
                    </div>
                  )}

                  {selectedWig && (
                    <div
                      ref={wigRef}
                      className="absolute top-1/2 left-1/2 group"
                      style={{
                        transform: `translate(calc(-50% + ${wigTransform.x}px), calc(-50% + ${wigTransform.y}px)) rotate(${wigTransform.rotate}deg) scale(${wigTransform.scale})`,
                        touchAction: 'none'
                      }}
                    >
                      <div
                        className="relative cursor-move p-2"
                        onMouseDown={handleMouseDown}
                        onTouchStart={handleMouseDown}
                      >
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img src={selectedWig.src} alt="Причёска" className="w-[280px] h-[280px] object-contain pointer-events-none drop-shadow-2xl" />
                        <div
                          className="absolute bottom-0 right-0 w-8 h-8 bg-indigo-500 rounded-full border-2 border-white shadow-lg flex items-center justify-center cursor-se-resize opacity-0 group-hover:opacity-100 transition-opacity"
                          onMouseDown={handleResizeMouseDown}
                          onTouchStart={handleResizeMouseDown}
                        >
                          <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" /></svg>
                        </div>
                      </div>
                    </div>
                  )}

                  {!selectedWig && (
                    <div className="absolute inset-0 flex items-center justify-center bg-black/40 backdrop-blur-sm pointer-events-none">
                      <p className="text-white text-lg font-medium px-6 py-3 bg-black/50 rounded-full">Выбери причёску из галереи →</p>
                    </div>
                  )}
                </>
              ) : stream ? (
                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  muted
                  onCanPlay={() => setCameraReady(true)}
                  className="w-full h-full object-cover scale-x-[-1]"
                  style={{ minHeight: '480px' }}
                />
              ) : (
                <div className="absolute inset-0 flex flex-col items-center justify-center gap-4 text-neutral-500">
                  <svg className="w-20 h-20 opacity-30" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
                  <p className="text-lg font-medium text-neutral-400">Загрузи фото или включи камеру</p>
                </div>
              )}

              <canvas ref={canvasRef} className="hidden" />
            </div>

            {/* Кнопки управления */}
            <div className="flex flex-wrap gap-3">
              {!userImage ? (
                <>
                  {!stream ? (
                    <button onClick={startCamera} className="flex-1 min-w-[140px] px-5 py-3.5 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold rounded-2xl shadow-lg transition-all active:scale-95 flex items-center justify-center gap-2">
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
                      Включить камеру
                    </button>
                  ) : (
                    <button
                      onClick={takePhoto}
                      disabled={!cameraReady}
                      className="flex-1 min-w-[140px] px-5 py-3.5 bg-green-500 hover:bg-green-400 disabled:bg-neutral-700 disabled:cursor-not-allowed text-white font-semibold rounded-2xl shadow-lg transition-all active:scale-95 flex items-center justify-center gap-2"
                    >
                      {cameraReady ? (
                        <>
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" /></svg>
                          Сделать снимок
                        </>
                      ) : (
                        <>
                          <svg className="w-5 h-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v3m0 12v3m9-9h-3M6 12H3m15.364-6.364l-2.121 2.121M8.757 15.243l-2.121 2.121m0-12.728l2.121 2.121M15.243 15.243l2.121 2.121"/></svg>
                          Камера загружается...
                        </>
                      )}
                    </button>
                  )}
                  <div className="flex items-center text-neutral-600 font-bold text-sm px-1">ИЛИ</div>
                  <button onClick={() => fileInputRef.current?.click()} className="flex-1 min-w-[140px] px-5 py-3.5 bg-neutral-800 hover:bg-neutral-700 border border-neutral-700 text-white font-semibold rounded-2xl transition-all active:scale-95 flex items-center justify-center gap-2">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" /></svg>
                    Загрузить фото
                  </button>
                </>
              ) : (
                <>
                  <button onClick={reset} className="px-5 py-3.5 bg-neutral-800 hover:bg-neutral-700 text-white font-semibold rounded-2xl transition-all active:scale-95 flex items-center justify-center gap-2">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
                    Начать заново
                  </button>
                  <button onClick={() => fileInputRef.current?.click()} className="px-5 py-3.5 bg-neutral-800 hover:bg-neutral-700 border border-neutral-700 text-white font-semibold rounded-2xl transition-all active:scale-95 flex items-center justify-center gap-2">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" /></svg>
                    Другое фото
                  </button>
                  <button onClick={handleExport} className="flex-1 px-5 py-3.5 bg-indigo-600 hover:bg-indigo-500 text-white font-bold rounded-2xl shadow-lg transition-all active:scale-95 flex items-center justify-center gap-2">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
                    Сохранить фото
                  </button>
                </>
              )}
              <input type="file" accept="image/*" ref={fileInputRef} onChange={handleFileUpload} className="hidden" />
            </div>

            {/* Настройка парика (под редактором) */}
            {selectedWig && userImage && (
              <div className="bg-neutral-800/80 backdrop-blur border border-neutral-700 p-5 rounded-3xl shadow-xl flex flex-col gap-4">
                <div className="flex items-center gap-2">
                  <svg className="w-4 h-4 text-indigo-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" /></svg>
                  <span className="font-bold">Настройка</span>
                  <span className="text-indigo-300 text-sm font-medium ml-1">— {selectedWig.name}</span>
                </div>
                <div className="grid grid-cols-2 gap-x-6 gap-y-4">
                  <div className="flex flex-col gap-2">
                    <div className="flex justify-between text-sm font-medium text-neutral-300">
                      <span>Размер</span>
                      <span className="text-indigo-400">{(wigTransform.scale * 100).toFixed(0)}%</span>
                    </div>
                    <input
                      type="range" min="0.2" max="5" step="0.05"
                      value={wigTransform.scale}
                      onChange={(e) => setWigTransform(p => ({ ...p, scale: parseFloat(e.target.value) }))}
                      className="w-full accent-indigo-500 h-2 rounded-lg appearance-none cursor-pointer"
                    />
                    <p className="text-[11px] text-neutral-500">Колёсико мыши или потяни за уголок</p>
                  </div>
                  <div className="flex flex-col gap-2">
                    <div className="flex justify-between text-sm font-medium text-neutral-300">
                      <span>Поворот</span>
                      <span className="text-indigo-400">{wigTransform.rotate}°</span>
                    </div>
                    <input
                      type="range" min="-180" max="180" step="1"
                      value={wigTransform.rotate}
                      onChange={(e) => setWigTransform(p => ({ ...p, rotate: parseFloat(e.target.value) }))}
                      className="w-full accent-indigo-500 h-2 rounded-lg appearance-none cursor-pointer"
                    />
                  </div>
                </div>
              </div>
            )}

            {/* ── AI Улучшение ── */}
            {userImage && (
              <div className="bg-neutral-800/80 backdrop-blur border border-neutral-700 p-5 rounded-3xl shadow-xl flex flex-col gap-4">
                <div className="flex items-center gap-2">
                  <svg className="w-5 h-5 text-violet-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"/>
                  </svg>
                  <span className="font-bold text-white">AI Улучшение</span>
                  <span className="text-xs text-violet-400 bg-violet-500/10 border border-violet-500/20 px-2 py-0.5 rounded-full ml-1">Gemini</span>
                </div>

                <textarea
                  value={aiPrompt}
                  onChange={e => setAiPrompt(e.target.value)}
                  placeholder={selectedWig
                    ? `Оставь пустым — AI сам применит причёску «${selectedWig.name}». Или напиши что изменить дополнительно...`
                    : 'Опиши что сделать с фото: поменять причёску, цвет волос, стиль... Или выбери парик из галереи справа.'}
                  rows={3}
                  className="w-full px-4 py-3 bg-neutral-700/50 border border-neutral-600 rounded-2xl text-sm text-white placeholder-neutral-500 focus:outline-none focus:border-violet-500 transition-colors resize-none"
                />

                <div className="flex gap-3 items-start">
                  <button
                    onClick={handleAiImprove}
                    disabled={aiLoading}
                    className="flex-1 px-5 py-3.5 bg-violet-600 hover:bg-violet-500 disabled:bg-neutral-700 disabled:cursor-not-allowed text-white font-bold rounded-2xl shadow-lg transition-all active:scale-95 flex items-center justify-center gap-2"
                  >
                    {aiLoading ? (
                      <>
                        <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/></svg>
                        Генерирую...
                      </>
                    ) : (
                      <>
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"/>
                        </svg>
                        Улучшить с AI
                      </>
                    )}
                  </button>
                  {aiResult && (
                    <a
                      href={aiResult}
                      download="ai-hairstyle.jpg"
                      className="px-5 py-3.5 bg-neutral-700 hover:bg-neutral-600 text-white font-semibold rounded-2xl transition-all active:scale-95 flex items-center justify-center gap-2 shrink-0"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/></svg>
                      Скачать
                    </a>
                  )}
                </div>

                {/* Результат AI */}
                {aiResult && (
                  <div className="flex flex-col gap-2">
                    <p className="text-xs text-neutral-500 font-medium">Результат AI:</p>
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={aiResult}
                      alt="AI результат"
                      className="w-full rounded-2xl border border-violet-500/30 shadow-lg"
                    />
                    <button
                      onClick={() => { setUserImage(aiResult); setAiResult(null); }}
                      className="w-full px-4 py-2.5 bg-violet-600/20 hover:bg-violet-600/30 border border-violet-500/30 text-violet-300 text-sm font-semibold rounded-xl transition-all"
                    >
                      Использовать как основное фото
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* ── Правая колонка: галерея ── */}
          <div className="w-full lg:w-88 xl:w-96 flex flex-col gap-4 lg:sticky lg:top-20">
            <div className="bg-neutral-800/80 backdrop-blur border border-neutral-700 p-5 rounded-3xl shadow-xl flex flex-col gap-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-bold">Коллекция причёсок</h3>
                <span className="text-xs font-semibold px-2 py-1 bg-indigo-500/20 text-indigo-300 rounded-full">
                  {AVAILABLE_WIGS.filter(w =>
                    (selectedCategory === 'all' || w.category === selectedCategory) &&
                    w.name.toLowerCase().includes(searchQuery.toLowerCase())
                  ).length} стилей
                </span>
              </div>

              <div className="flex flex-wrap gap-1.5">
                {CATEGORIES.map(cat => (
                  <button
                    key={cat.id}
                    onClick={() => setSelectedCategory(cat.id)}
                    className={`px-2.5 py-1.5 rounded-xl text-[10px] font-bold uppercase tracking-wider transition-all ${selectedCategory === cat.id ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-500/20' : 'bg-neutral-700/50 text-neutral-400 hover:text-neutral-200 hover:bg-neutral-700'}`}
                  >
                    {cat.label}
                  </button>
                ))}
              </div>

              <div className="relative">
                <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
                </svg>
                <input
                  type="text"
                  placeholder="Поиск причёски..."
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                  className="w-full pl-9 pr-4 py-2 bg-neutral-700/50 border border-neutral-600 rounded-xl text-sm text-white placeholder-neutral-500 focus:outline-none focus:border-indigo-500 transition-colors"
                />
              </div>

              <div className="grid grid-cols-3 gap-2.5 overflow-y-auto pr-1 custom-scrollbar" style={{ maxHeight: 'calc(100vh - 340px)' }}>
                {AVAILABLE_WIGS
                  .filter(w =>
                    (selectedCategory === 'all' || w.category === selectedCategory) &&
                    w.name.toLowerCase().includes(searchQuery.toLowerCase())
                  )
                  .map((wig) => (
                  <button
                    key={wig.id}
                    title={wig.name}
                    onClick={async () => {
                      setSelectedWig(wig);
                      if (userImage) {
                        const t = await getDefaultWigTransform();
                        setWigTransform(t);
                      }
                    }}
                    className={`relative aspect-square flex flex-col items-center border-2 rounded-2xl overflow-hidden transition-all group ${selectedWig?.id === wig.id ? 'border-indigo-500 bg-indigo-500/10 scale-95 shadow-inner' : 'border-neutral-700/50 bg-neutral-700/30 hover:border-neutral-500 hover:bg-neutral-700/50'}`}
                  >
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={wig.src} alt={wig.name} className="w-full h-full object-contain drop-shadow-md p-1.5" />
                    <div className="absolute bottom-0 left-0 right-0 bg-black/70 text-[9px] text-center text-white py-1 px-1 leading-tight opacity-0 group-hover:opacity-100 transition-opacity truncate">
                      {wig.name}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>

        </div>
      </main>

      <style dangerouslySetInnerHTML={{__html: `
        .custom-scrollbar::-webkit-scrollbar { width: 5px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: rgba(0,0,0,0.1); border-radius: 10px; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 10px; }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.2); }
      `}} />
    </div>
  );
}
