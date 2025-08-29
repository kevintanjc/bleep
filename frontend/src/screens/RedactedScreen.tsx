import React from "react";
import { Gallery } from "@/components/Gallery";
import { useGallery } from "@/context/GalleryContext";

export default function RedactedScreen() {
  const { redacted } = useGallery();
  return <Gallery uris={redacted} />;
}