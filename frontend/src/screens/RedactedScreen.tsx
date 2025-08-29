import React from "react";
import { View } from "react-native";
import { useGallery } from "@/context/GalleryContext";
import { Gallery } from "@/components/Gallery";

export default function RedactedScreen() {
  const { state } = useGallery() as {
    state: { redacted: { uri: string }[] };
  };
  return (
    <View style={{ flex: 1 }}>
      <Gallery uris={(state.redacted || []).map(r => r.uri)} />
    </View>
  );
}
