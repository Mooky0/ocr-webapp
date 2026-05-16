import axios from "axios";

const api = axios.create({
  baseURL: "/backend",
});

export interface ImageSummary {
  id: string;
  filename: string;
  description: string;
  ocr_status: "pending" | "processing" | "completed" | "failed";
}

export interface OcrBox {
  text: string;
  left: number;
  top: number;
  width: number;
  height: number;
}

export interface ImageDetail {
  id: string;
  filename: string;
  description: string;
  ocr_text: string | null;
  ocr_boxes: OcrBox[] | null;
}

export async function listImages(): Promise<ImageSummary[]> {
  const { data } = await api.get<ImageSummary[]>("/images");
  return data;
}

export async function getImage(id: string): Promise<ImageDetail> {
  const { data } = await api.get<ImageDetail>(`/images/${id}`);
  return data;
}

export async function uploadImage(file: File, description: string): Promise<ImageSummary> {
  const form = new FormData();
  form.append("file", file);
  form.append("description", description);
  const { data } = await api.post<ImageSummary>("/images", form);
  return data;
}

export async function notificationSubscribe(email:string) {
  const form = new FormData();
  form.append("email", email);
  try {
    const { data } = await api.post("/subscribe", form);
    return data;
  } catch (err) {
    if (axios.isAxiosError(err)) {
      throw new Error(err.response?.data?.detail ?? "Subscription failed.");
    }
    throw err;
  }
}

export function imageFileUrl(id: string): string {
  return `/backend/images/${id}/file`;
}
