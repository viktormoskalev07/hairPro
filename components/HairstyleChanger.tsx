'use client';

import { useState, useRef, useEffect } from 'react';
import Image from 'next/image';
import styles from './HairstyleChanger.module.css';

const hairstyles = [
  '/hairstyles/hairstyle1.png',
  '/hairstyles/hairstyle2.png',
  '/hairstyles/hairstyle3.png',
];

export default function HairstyleChanger() {
  const [userImage, setUserImage] = useState<string | null>(null);
  const [selectedHairstyle, setSelectedHairstyle] = useState<string | null>(null);
  const [finalImage, setFinalImage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [hairstyleTransform, setHairstyleTransform] = useState({
    scale: 1,
    rotate: 0,
    x: 0,
    y: 0,
  });
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      setStream(stream);
    } catch (err) {
      console.error("Error accessing camera: ", err);
      alert("Не удалось получить доступ к камере. Пожалуйста, проверьте разрешения.");
    }
  };

  const takePhoto = () => {
    if (videoRef.current && canvasRef.current) {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const context = canvas.getContext('2d');
      if (context) {
        context.drawImage(video, 0, 0, canvas.width, canvas.height);
        const dataUrl = canvas.toDataURL('image/png');
        setUserImage(dataUrl);
        stopCamera();
      }
    }
  };

  const handleImageUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        if (e.target?.result) {
          setUserImage(e.target.result as string);
          stopCamera();
        }
      };
      reader.readAsDataURL(file);
    }
  };

  const triggerFileUpload = () => {
    fileInputRef.current?.click();
  };

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      setStream(null);
      if (videoRef.current) {
          videoRef.current.srcObject = null;
      }
    }
  };

  const reset = () => {
    setUserImage(null);
    setSelectedHairstyle(null);
    setFinalImage(null);
    setIsLoading(false);
    setHairstyleTransform({ scale: 1, rotate: 0, x: 0, y: 0 });
    startCamera();
  };

  const handleHairstyleSelect = (hairstyle: string) => {
    setSelectedHairstyle(hairstyle);
    setHairstyleTransform({ scale: 1, rotate: 0, x: 0, y: 0 });
  };

  const handleTransformChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setHairstyleTransform(prev => ({
      ...prev,
      [name]: parseFloat(value),
    }));
  };

  const applyHairstyle = () => {
    if (!userImage || !selectedHairstyle) return;
    setIsLoading(true);
    // Simulate API call to process the image
    setTimeout(() => {
      // In a real app, you'd get a new image URL from the backend.
      // Here, we'll just use the user's image to represent the final result.
      // The selected hairstyle will still be overlaid.
      setFinalImage(userImage);
      setIsLoading(false);
    }, 2000);
  };

  const handleDownload = () => {
    if (!finalImage || !selectedHairstyle) return;

    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const userImg = new window.Image();
    userImg.crossOrigin = 'Anonymous';
    userImg.src = finalImage;

    userImg.onload = () => {
      // Set canvas dimensions to match the displayed image
      const displayWidth = 640;
      const displayHeight = 480;
      canvas.width = displayWidth;
      canvas.height = displayHeight;

      // Draw the user image, fitting it to the canvas
      ctx.drawImage(userImg, 0, 0, displayWidth, displayHeight);

      const hairstyleImg = new window.Image();
      hairstyleImg.crossOrigin = 'Anonymous';
      hairstyleImg.src = selectedHairstyle;

      hairstyleImg.onload = () => {
        // Calculate dimensions for 'object-fit: contain'
        const imgAspectRatio = hairstyleImg.naturalWidth / hairstyleImg.naturalHeight;
        const canvasAspectRatio = canvas.width / canvas.height;
        let renderWidth, renderHeight;

        if (imgAspectRatio > canvasAspectRatio) {
          renderWidth = canvas.width;
          renderHeight = canvas.width / imgAspectRatio;
        } else {
          renderHeight = canvas.height;
          renderWidth = canvas.height * imgAspectRatio;
        }

        ctx.save();
        const centerX = canvas.width / 2;
        const centerY = canvas.height / 2;
        ctx.translate(centerX, centerY);
        ctx.translate((canvas.width * hairstyleTransform.x) / 100, (canvas.height * hairstyleTransform.y) / 100);
        ctx.rotate((hairstyleTransform.rotate * Math.PI) / 180);
        ctx.scale(hairstyleTransform.scale, hairstyleTransform.scale);
        
        ctx.drawImage(hairstyleImg, -renderWidth / 2, -renderHeight / 2, renderWidth, renderHeight);
        ctx.restore();

        const link = document.createElement('a');
        link.download = 'hairstyle-makeover.png';
        link.href = canvas.toDataURL('image/png');
        link.click();
      };
    };
  };

  useEffect(() => {
    startCamera();
    return () => {
      stopCamera();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className={styles.container}>
      <h1 className={styles.title}>Примерка причесок</h1>
      <div className={styles.mainContent}>
        <div className={styles.cameraContainer}>
          {finalImage ? (
            <div className={styles.imagePreviewContainer}>
              <Image src={finalImage} alt="Результат" width={640} height={480} className={styles.userImage} />
              {selectedHairstyle && (
                <div 
                  className={styles.hairstyleOverlay}
                  style={{
                    transform: `translateX(${hairstyleTransform.x}%) translateY(${hairstyleTransform.y}%) rotate(${hairstyleTransform.rotate}deg) scale(${hairstyleTransform.scale})`,
                  }}
                >
                  <Image src={selectedHairstyle} alt="Выбранная прическа" layout="fill" objectFit="contain" />
                </div>
              )}
            </div>
          ) : userImage ? (
            <div className={styles.imagePreviewContainer}>
              <Image src={userImage} alt="Ваше фото" width={640} height={480} className={styles.userImage} />
              {selectedHairstyle && (
                <div 
                  className={styles.hairstyleOverlay}
                  style={{
                    transform: `translateX(${hairstyleTransform.x}%) translateY(${hairstyleTransform.y}%) rotate(${hairstyleTransform.rotate}deg) scale(${hairstyleTransform.scale})`,
                  }}
                >
                   <Image src={selectedHairstyle} alt="Выбранная прическа" layout="fill" objectFit="contain" />
                </div>
              )}
              {isLoading && (
                <div className={styles.loadingOverlay}>
                  <span>Обработка...</span>
                </div>
              )}
            </div>
          ) : (
            <video ref={videoRef} autoPlay playsInline className={styles.video} />
          )}
          <canvas ref={canvasRef} style={{ display: 'none' }} />
        </div>
        
        <div className={styles.controls}>
          {finalImage ? (
            <div className={styles.finalActions}>
              <button onClick={reset} className={styles.button}>
                Начать заново
              </button>
              <button onClick={handleDownload} className={styles.button}>
                Скачать результат
              </button>
            </div>
          ) : !userImage ? (
            <>
              <button onClick={takePhoto} className={styles.button} disabled={!stream}>
                Сделать фото
              </button>
              <button onClick={triggerFileUpload} className={styles.button}>
                Загрузить фото
              </button>
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleImageUpload}
                style={{ display: 'none' }}
                accept="image/*"
              />
            </>
          ) : (
            <button onClick={reset} className={styles.button}>
              Переделать фото
            </button>
          )}
        </div>
      </div>
      
      {userImage && !finalImage && (
        <div className={styles.hairstyleSelector}>
          <h2>Выберите прическу</h2>
          <div className={styles.hairstyleGrid}>
            {hairstyles.map((hairstyle, index) => (
              <div 
                key={index} 
                className={`${styles.hairstyleItem} ${selectedHairstyle === hairstyle ? styles.hairstyleItemSelected : ''}`} 
                onClick={() => handleHairstyleSelect(hairstyle)}
              >
                <Image src={hairstyle} alt={`Прическа ${index + 1}`} width={100} height={100} />
              </div>
            ))}
          </div>
          {selectedHairstyle && (
            <div className={styles.transformControls}>
              <h4>Настроить прическу</h4>
              <div className={styles.controlGroup}>
                <label>Размер:</label>
                <input type="range" name="scale" min="0.5" max="2" step="0.05" value={hairstyleTransform.scale} onChange={handleTransformChange} />
              </div>
              <div className={styles.controlGroup}>
                <label>Поворот:</label>
                <input type="range" name="rotate" min="-45" max="45" step="1" value={hairstyleTransform.rotate} onChange={handleTransformChange} />
              </div>
              <div className={styles.controlGroup}>
                <label>По горизонтали:</label>
                <input type="range" name="x" min="-50" max="50" step="1" value={hairstyleTransform.x} onChange={handleTransformChange} />
              </div>
              <div className={styles.controlGroup}>
                <label>По вертикали:</label>
                <input type="range" name="y" min="-50" max="50" step="1" value={hairstyleTransform.y} onChange={handleTransformChange} />
              </div>
            </div>
          )}
          <div className={styles.hairstyleActions}>
            <button onClick={() => setSelectedHairstyle(null)} className={styles.buttonClear}>
                Убрать прическу
            </button>
            <button onClick={applyHairstyle} className={styles.button} disabled={!selectedHairstyle || isLoading}>
              {isLoading ? 'Обработка...' : 'Применить прическу'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
