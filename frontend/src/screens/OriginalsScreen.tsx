import React, { useState, useMemo } from "react";
import { View, Button, Text } from "react-native";
import * as ImagePicker from "expo-image-picker";
import * as FileSystem from "expo-file-system";
import { useGallery } from "src/gallery/GalleryContext";
import { useInspector } from "src/inspect/InspectorContext";
import { Gallery } from "src/gallery/Gallery";
import { sendImageForRedaction } from "@/api/redact";

function makeId() {
  return Math.random().toString(36).slice(2);
}

async function toUniqueFileUri(srcUri: string, ext = "jpg") {
  const id = Date.now().toString(36) + "_" + Math.random().toString(36).slice(2);
  const dst = `${FileSystem.cacheDirectory}orig_${id}.${ext}`;
  await FileSystem.copyAsync({ from: srcUri, to: dst });
  const info = await FileSystem.getInfoAsync(dst);
  if (!info.exists || !info.size) throw new Error("copy failed");
  return dst; // file://...
}

export default function OriginalsScreen() {
  const { state, addOriginal, addRedacted } = useGallery();
  const [status, setStatus] = useState("");
  const { open } = useInspector()

  const uris = useMemo(() => state.originals.map(o => o.uri), [state.originals]);
  const items = useMemo(() => uris.map(u => ({ uri: u })), [uris]); 

  async function pick() {
    setStatus("");
    const r = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 1
    });
    if (r.canceled || !r.assets?.[0]?.uri) return;

    // Always normalize to a fresh file:// path to avoid content:// and cache reuse
    const pickedUri = r.assets[0].uri;
    const ext = (pickedUri.split(".").pop() || "jpg").toLowerCase();
    let origFileUri = pickedUri;
    try {
      origFileUri = await toUniqueFileUri(pickedUri, ext);
    } catch {
      // fall back to picker URI if copy fails
    }

    const id = makeId();
    addOriginal({ id, uri: origFileUri, createdAt: Date.now(), name: "original" });

    try {
      setStatus("Redacting...");
      // Ensure your sendImageForRedaction writes a unique file and returns file://... with ?t= cache buster
      const res = await sendImageForRedaction(origFileUri);
      const redId = `${id}_${Date.now()}`;
      addRedacted({
        id: redId,
        originalId: id,
        uri: res.uri,           // expect file://...?...t=timestamp
        applied: res.applied,
        createdAt: Date.now()
      });
      setStatus(res.applied ? "Redacted" : "No redactions found");
    } catch (e: any) {
      setStatus(`Redaction failed: ${e.message}`);
    }
  }

  return (
    <View style={{ flex: 1 }}>
      <Button title="Add photo" onPress={pick} />
      <Gallery 
        uris={state.originals.map(o => o.uri)} 
        onPress={(index) => open(items, index)}
      />
    </View>
  );
}
