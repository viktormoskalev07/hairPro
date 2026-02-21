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
  const [stream, setStream] = useState<MediaStream | null>(null);
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
    startCamera();
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
          {userImage ? (
            <div className={styles.imagePreviewContainer}>
              <Image src={userImage} alt="Ваше фото" width={640} height={480} className={styles.userImage} />
              {selectedHairstyle && (
                <div className={styles.hairstyleOverlay}>
                   <Image src={selectedHairstyle} alt="Выбранная прическа" layout="fill" objectFit="contain" />
                </div>
              )}
            </div>
          ) : (
            <video ref={videoRef} autoPlay playsInline className={styles.video} />
          )}
          <canvas ref={canvasRef} style={{ display: 'none' }} />
        </div>
        
        <div className={styles.controls}>
          {!userImage ? (
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
      
      {userImage && (
        <div className={styles.hairstyleSelector}>
          <h2>Выберите прическу</h2>
          <div className={styles.hairstyleGrid}>
            {hairstyles.map((hairstyle, index) => (
              <div key={index} className={styles.hairstyleItem} onClick={() => setSelectedHairstyle(hairstyle)}>
                <Image src={hairstyle} alt={`Прическа ${index + 1}`} width={100} height={100} />
              </div>
            ))}
          </div>
           <button onClick={() => setSelectedHairstyle(null)} className={styles.buttonClear}>
              Убрать прическу
            </button>
        </div>
      )}
    </div>
  );
}
