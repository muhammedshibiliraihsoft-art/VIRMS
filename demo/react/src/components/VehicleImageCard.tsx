import React, { useState } from 'react';
import { Car, ImageOff } from 'lucide-react';

interface VehicleImageCardProps {
  imageUrl?: string | null;
  altText?: string;
  className?: string;
}

export const VehicleImageCard: React.FC<VehicleImageCardProps> = ({
  imageUrl,
  altText = 'Vehicle Photo',
  className = '',
}) => {
  const [imageError, setImageError] = useState(false);

  const hasValidImage = Boolean(imageUrl && !imageError);

  return (
    <div
      className={`dashboard-card-solid rounded-[26px] p-2 flex flex-col justify-center items-center h-full min-h-[84px] max-h-[96px] relative overflow-hidden group select-none ${className}`}
    >
      {hasValidImage ? (
        <div className="w-full h-full rounded-[18px] overflow-hidden bg-white/90 dark:bg-zinc-900/60 flex items-center justify-center border border-[#ece4dc] dark:border-zinc-700/60 relative">
          <img
            src={imageUrl!}
            alt={altText}
            onError={() => setImageError(true)}
            className="w-full h-full object-contain p-1 group-hover:scale-105 transition-transform duration-300"
            loading="lazy"
          />
          {/* Subtle bottom-right model tag */}
          <div className="absolute bottom-1 right-1.5 px-1.5 py-0.5 rounded-md bg-black/60 dark:bg-white/80 text-white dark:text-black text-[8px] font-bold backdrop-blur-none">
            Vehicle
          </div>
        </div>
      ) : (
        /* Clean minimal placeholder when no image exists */
        <div className="w-full h-full rounded-[18px] bg-gradient-to-br from-[#f8f5f2] to-[#f2ece5] dark:from-zinc-800/80 dark:to-zinc-850 border border-dashed border-[#e6ddd4] dark:border-zinc-700 flex flex-col items-center justify-center gap-1 p-2 text-center">
          <div className="w-6 h-6 rounded-full bg-white dark:bg-zinc-800 shadow-2xs border border-[#eee6de] dark:border-zinc-700 flex items-center justify-center text-gray-400 dark:text-gray-300">
            <Car className="w-3.5 h-3.5 text-[var(--theme-primary)]" />
          </div>
          <span className="text-[10px] font-bold text-gray-500 dark:text-gray-400 leading-none">
            No vehicle image
          </span>
        </div>
      )}
    </div>
  );
};
