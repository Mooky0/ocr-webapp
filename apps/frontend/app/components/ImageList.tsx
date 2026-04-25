"use client";

import {
  Box,
  Card,
  CardActionArea,
  CardMedia,
  CardContent,
  CircularProgress,
  Grid,
  Typography,
} from "@mui/material";
import { ImageSummary, imageFileUrl } from "../lib/api";

interface Props {
  images: ImageSummary[];
  loading: boolean;
  selectedId: string | null;
  onSelect: (id: string) => void;
}

export default function ImageList({ images, loading, selectedId, onSelect }: Props) {
  if (loading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (images.length === 0) {
    return (
      <Typography sx={{ color: "text.secondary", textAlign: "center", py: 4 }}>
        No images yet. Upload one to get started.
      </Typography>
    );
  }

  return (
    <Grid container spacing={2}>
      {images.map((img) => (
        <Grid key={img.id} size={{ xs: 6, sm: 4, md: 3 }}>
          <Card
            variant="outlined"
            sx={{
              outline: selectedId === img.id ? "2px solid" : "none",
              outlineColor: "primary.main",
            }}
          >
            <CardActionArea onClick={() => onSelect(img.id)}>
              <CardMedia
                component="img"
                height={120}
                image={imageFileUrl(img.id)}
                alt={img.filename}
                sx={{ objectFit: "cover" }}
              />
              <CardContent sx={{ py: 1, px: 1.5 }}>
                <Typography variant="caption" sx={{ display: "block", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {img.description}
                </Typography>
                <Typography variant="body2" sx={{ color: "text.secondary", mt: 1 }}>
                  {img.filename}
                </Typography>
              </CardContent>
            </CardActionArea>
          </Card>
        </Grid>
      ))}
    </Grid>
  );
}
