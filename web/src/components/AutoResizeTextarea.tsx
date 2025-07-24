import React, { useEffect, useRef, useCallback } from 'react';

interface AutoResizeTextareaProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
  style?: React.CSSProperties;
  minRows?: number;
  maxRows?: number;
  disabled?: boolean;
}

export const AutoResizeTextarea: React.FC<AutoResizeTextareaProps> = ({
  value,
  onChange,
  placeholder,
  className = '',
  style,
  minRows = 2,
  maxRows = 10,
  disabled = false
}) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const adjustHeight = useCallback(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    // Reset height to auto to get the correct scrollHeight
    textarea.style.height = 'auto';
    
    // Get the scrollHeight (total content height)
    const scrollHeight = textarea.scrollHeight;
    
    // Get line height from computed styles
    const styles = window.getComputedStyle(textarea);
    const lineHeight = parseInt(styles.lineHeight) || 20;
    
    // Calculate number of lines in content
    const contentLines = Math.ceil(scrollHeight / lineHeight);
    
    // Ensure we stay within min/max bounds
    const targetLines = Math.max(minRows, Math.min(maxRows, contentLines));
    
    // Set the height to the target number of lines
    textarea.style.height = `${targetLines * lineHeight}px`;
  }, [minRows, maxRows]);

  useEffect(() => {
    adjustHeight();
  }, [value, adjustHeight]);

  useEffect(() => {
    // Initial adjustment
    const timer = setTimeout(adjustHeight, 0);
    return () => clearTimeout(timer);
  }, [adjustHeight]);

  return (
    <textarea
      ref={textareaRef}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      className={`resize-none overflow-hidden ${className}`}
      style={{
        minHeight: `${minRows * 1.5}rem`,
        maxHeight: `${maxRows * 1.5}rem`,
        ...style
      }}
      onInput={adjustHeight}
      rows={minRows}
      disabled={disabled}
    />
  );
};