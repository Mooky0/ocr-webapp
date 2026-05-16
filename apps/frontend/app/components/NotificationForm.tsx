"use client";

import { useState } from "react";
import {
  Box,
  Button,
  CircularProgress,
  Stack,
  TextField,
  Typography,
  Alert,
} from "@mui/material";
import { notificationSubscribe } from "../lib/api";

interface Props {
  onUploaded: () => void;
}

export default function NotificationForm({ onUploaded: onSubscribed }: Props) {
  const [emailAddress, setEmailAddress] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setInfo(null);
    try {
      await notificationSubscribe(emailAddress);
      setEmailAddress("");
      onSubscribed();
    } catch (err) {
      const message = err instanceof Error ? err.message : "Subscription failed.";
      if (message === "Email already subscribed") {
        setInfo("You're already subscribed — you'll receive notifications.");
      } else {
        setError(message);
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <Box component="form" onSubmit={handleSubmit}>
      <Stack spacing={2}>

        <TextField
          label="Email address"
          value={emailAddress}
          onChange={(e) => setEmailAddress(e.target.value)}
          required
          size="small"
        />

        {error && <Alert severity="error">{error}</Alert>}
        {info && <Alert severity="info">{info}</Alert>}

        <Button
          type="submit"
          variant="contained"
          disabled={!emailAddress || loading}
          startIcon={loading ? <CircularProgress size={16} /> : undefined}
        >
          {loading ? "Subscribing…" : "Subscribe"}
        </Button>

        {loading && (
          <Typography variant="caption" sx={{ color: "text.secondary" }}>
            This may take a moment. You will receive an email when the OCR is done.
          </Typography>
        )}
      </Stack>
    </Box>
  );
}
