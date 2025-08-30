import React from "react";
import { View } from "react-native";
import { Gallery } from "src/gallery/Gallery";
import { useInspector } from "src/inspect/InspectorContext";
import { useGallery } from "src/gallery/GalleryContext";

export default function RedactedScreen() {
  const { state } = useGallery() as {
    state: { redacted: { uri: string }[] };
  };
  const { open } = useInspector();
  const uris = (state.redacted || []).map(r => r.uri);
  return (
    <View style={{ flex: 1 }}>
      <Gallery 
        uris={(state.redacted || []).map(r => r.uri)} 
        onPress={(index) => open(uris.map(u => ({ uri: u })), index)}
      />
    </View>
  );
}
