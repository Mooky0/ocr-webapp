"use client";

import { useEffect, useState, useRef } from "react";
import {
  Box,
  CircularProgress,
  Chip,
  Divider,
  IconButton,
  Stack,
  Tooltip,
  Typography,
} from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import { getImage, imageFileUrl, ImageDetail as Detail, OcrBox } from "../lib/api";

interface Props {
  id: string;
  onClose: () => void;
}

export default function ImageDetail({ id, onClose }: Props) {
  const [detail, setDetail] = useState<Detail | null>(null);
  const [imgSize, setImgSize] = useState<{ w: number; h: number } | null>(null);
  const [naturalSize, setNaturalSize] = useState<{ w: number; h: number } | null>(null);
  const imgRef = useRef<HTMLImageElement>(null);

  useEffect(() => {
    getImage(id).then(setDetail);
  }, [id]);

  function handleImageLoad() {
    const img = imgRef.current;
    if (!img) return;
    setImgSize({ w: img.clientWidth, h: img.clientHeight });
    setNaturalSize({ w: img.naturalWidth, h: img.naturalHeight });
  }

  function scaleBox(box: OcrBox) {
    if (!imgSize || !naturalSize) return null;
    const scaleX = imgSize.w / naturalSize.w;
    const scaleY = imgSize.h / naturalSize.h;
    return {
      left: box.left * scaleX,
      top: box.top * scaleY,
      width: box.width * scaleX,
      height: box.height * scaleY,
    };
  }

  if (!detail) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Stack spacing={2}>
      <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <Typography variant="h6" sx={{ maxWidth: "80%", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {detail.description}
        </Typography>
        <IconButton onClick={onClose} size="small">
          <CloseIcon />
        </IconButton>
      </Box>

      <Typography variant="body2" sx={{ color: "text.secondary" }}>
        {detail.filename}
      </Typography>

      <Box sx={{ position: "relative", display: "inline-block", width: "100%" }}>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          ref={imgRef}
          src={imageFileUrl(id)}
          alt={detail.filename}
          onLoad={handleImageLoad}
          style={{ width: "100%", display: "block", borderRadius: 4 }}
        />
        {imgSize &&
          naturalSize &&
          detail.ocr_boxes?.map((box, i) => {
            const scaled = scaleBox(box);
            if (!scaled) return null;
            return (
              <Tooltip key={i} title={box.text} placement="top" arrow>
                <Box
                  sx={{
                    position: "absolute",
                    left: scaled.left,
                    top: scaled.top,
                    width: scaled.width,
                    height: scaled.height,
                    border: "1.3px solid",
                    borderColor: "primary.main",
                    borderRadius: "2px",
                    cursor: "default",
                    "&:hover": { bgcolor: "primary.main", opacity: 0.25 },
                  }}
                />
              </Tooltip>
            );
          })}
      </Box>

      {detail.ocr_text && (
        <>
          <Divider />
          <Typography variant="subtitle2" sx={{ color: "text.secondary" }}>
            Detected text
          </Typography>
          <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5 }}>
            {detail.ocr_boxes?.map((box, i) => (
              <Chip key={i} label={box.text} size="small" variant="outlined" />
            ))}
          </Box>
        </>
      )}
    </Stack>
  );
}
