import type { Metadata } from "next";
import ThemeRegistry from "./components/ThemeRegistry";

export const metadata: Metadata = {
  title: "OCR Web App",
  description: "Upload images and run OCR",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <ThemeRegistry>{children}</ThemeRegistry>
      </body>
    </html>
  );
}
