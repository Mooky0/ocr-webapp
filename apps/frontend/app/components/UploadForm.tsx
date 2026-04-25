"use client";

import { useState, useRef } from "react";
import {
  Box,
  Button,
  CircularProgress,
  Stack,
  TextField,
  Typography,
  Alert,
} from "@mui/material";
import UploadFileIcon from "@mui/icons-material/UploadFile";
import { uploadImage } from "../lib/api";

interface Props {
  onUploaded: () => void;
}

export default function UploadForm({ onUploaded }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      await uploadImage(file, description);
      setFile(null);
      setDescription("");
      if (inputRef.current) inputRef.current.value = "";
      onUploaded();
    } catch {
      setError("Upload failed. Make sure the backend is running.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Box component="form" onSubmit={handleSubmit}>
      <Stack spacing={2}>
        <Button
          variant="outlined"
          component="label"
          startIcon={<UploadFileIcon />}
        >
          {file ? file.name : "Choose image"}
          <input
            ref={inputRef}
            type="file"
            accept="image/*"
            hidden
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
        </Button>

        <TextField
          label="Description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          required
          size="small"
        />

        {error && <Alert severity="error">{error}</Alert>}

        <Button
          type="submit"
          variant="contained"
          disabled={!file || !description || loading}
          startIcon={loading ? <CircularProgress size={16} /> : undefined}
        >
          {loading ? "Uploading…" : "Upload & Run OCR"}
        </Button>

        {loading && (
          <Typography variant="caption" sx={{ color: "text.secondary" }}>
            Running OCR, this may take a moment…
          </Typography>
        )}
      </Stack>
    </Box>
  );
}
