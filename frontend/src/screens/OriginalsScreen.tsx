import React, { useState } from "react";
import { Alert, Button, View } from "react-native";
import * as ImagePicker from "expo-image-picker";
import { useGallery } from "@/context/GalleryContext";
import { sendImageForRedaction } from "@/api/redact";
import { saveBytesToCache } from "@/utils/image";
import { Gallery } from "@/components/Gallery";

export default function OriginalsScreen() {
  const { originals, addOriginal, addRedacted } = useGallery();
  const [refreshing, setRefreshing] = useState(false);

  async function pickAndProcess() {
    const res = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 1
    });
    if (res.canceled || !res.assets?.[0]?.uri) return;

    const originalUri = res.assets[0].uri;
    addOriginal(originalUri);

    setRefreshing(true);
    try {
      const { bytes, applied } = await sendImageForRedaction(originalUri);

      if (applied) {
        const name = `redacted_${Date.now()}.jpg`;
        const redactedUri = await saveBytesToCache(bytes, name);
        addRedacted(redactedUri);
      } else {
        // No redactions, mirror the original into Redacted
        addRedacted(originalUri);
      }
      Alert.alert("Done", applied ? "Redactions applied" : "No redactions found");
    } catch (e: any) {
      Alert.alert("Upload failed", e.message ?? String(e));
    } finally {
      setRefreshing(false);
    }
  }

  return (
    <View style={{ flex: 1 }}>
      <Button title="Pick & Redact" onPress={pickAndProcess} />
      <Gallery uris={originals} refreshing={refreshing} />
    </View>
  );
}
