import React, { useState, useRef } from 'react';
import { UploadCloud, FileText, AlertCircle, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface FileUploadProps {
  onFileSelect: (file: File) => void;
  acceptedFormats?: string[];
  maxSizeMB?: number;
  isUploading?: boolean;
  uploadProgress?: number;
  className?: string;
}

export const FileUpload: React.FC<FileUploadProps> = ({
  onFileSelect,
  acceptedFormats = ['.pdf', '.docx'],
  maxSizeMB = 10,
  isUploading = false,
  uploadProgress = 0,
  className = '',
}) => {
  const [dragActive, setDragActive] = useState<boolean>(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const validateFile = (file: File): boolean => {
    setError(null);
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!acceptedFormats.includes(ext)) {
      setError(`Invalid format (${ext}). Supported: ${acceptedFormats.join(', ')}`);
      return false;
    }
    const maxSizeBytes = maxSizeMB * 1024 * 1024;
    if (file.size > maxSizeBytes) {
      setError(`File is too large (${(file.size / (1024 * 1024)).toFixed(1)}MB). Max: ${maxSizeMB}MB`);
      return false;
    }
    return true;
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (validateFile(file)) {
        setSelectedFile(file);
        onFileSelect(file);
      }
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (validateFile(file)) {
        setSelectedFile(file);
        onFileSelect(file);
      }
    }
  };

  const removeFile = (e: React.MouseEvent) => {
    e.stopPropagation();
    setSelectedFile(null);
    setError(null);
    if (inputRef.current) {
      inputRef.current.value = '';
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024 * 1024) {
      return (bytes / 1024).toFixed(1) + ' KB';
    }
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <div className={`w-full ${className}`}>
      <input
        ref={inputRef}
        type="file"
        accept={acceptedFormats.join(',')}
        onChange={handleChange}
        className="hidden"
      />

      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={`relative border-2 border-dashed rounded-3xl p-8 transition-all duration-300 cursor-pointer text-center ${
          dragActive
            ? 'border-violet-500 bg-violet-500/10 scale-[1.01]'
            : 'border-white/10 hover:border-violet-500/40 bg-slate-900/40 hover:bg-slate-900/60'
        } ${selectedFile ? 'border-violet-500/60 bg-violet-950/20' : ''}`}
      >
        <div className="flex flex-col items-center justify-center">
          <div
            className={`w-16 h-16 rounded-2xl flex items-center justify-center mb-4 transition-transform duration-300 ${
              dragActive ? 'scale-110 bg-violet-600 text-white' : 'bg-violet-600/10 text-violet-400 border border-violet-500/20'
            }`}
          >
            {selectedFile ? (
              <FileText className="w-8 h-8 text-violet-400" />
            ) : (
              <UploadCloud className="w-8 h-8" />
            )}
          </div>

          {!selectedFile ? (
            <>
              <p className="text-base font-semibold text-white mb-1">
                Drag & drop your resume here, or <span className="text-violet-400 underline">browse</span>
              </p>
              <p className="text-xs text-slate-400">
                Supports {acceptedFormats.map((f) => f.toUpperCase().replace('.', '')).join(', ')} up to {maxSizeMB}MB
              </p>
            </>
          ) : (
            <div className="flex items-center gap-3 max-w-full px-4 py-2 bg-slate-800/80 rounded-xl border border-white/10">
              <FileText className="w-5 h-5 text-violet-400 shrink-0" />
              <div className="text-left overflow-hidden">
                <p className="text-sm font-medium text-white truncate max-w-xs">{selectedFile.name}</p>
                <p className="text-xs text-slate-400">{formatFileSize(selectedFile.size)}</p>
              </div>
              <button
                type="button"
                onClick={removeFile}
                className="p-1 rounded-lg hover:bg-white/10 text-slate-400 hover:text-white transition-colors ml-2"
                title="Remove file"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          )}

          {/* Upload progress */}
          <AnimatePresence>
            {isUploading && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="w-full max-w-xs mt-6 space-y-2"
              >
                <div className="flex justify-between text-xs font-medium text-slate-300">
                  <span>Uploading & extracting...</span>
                  <span>{uploadProgress}%</span>
                </div>
                <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                  <motion.div
                    className="h-full bg-gradient-to-r from-violet-500 to-blue-500"
                    style={{ width: `${uploadProgress}%` }}
                    transition={{ ease: 'linear' }}
                  />
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {error && (
        <motion.div
          initial={{ opacity: 0, y: -5 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-3 flex items-center gap-2 text-rose-400 text-xs px-2"
        >
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </motion.div>
      )}
    </div>
  );
};
