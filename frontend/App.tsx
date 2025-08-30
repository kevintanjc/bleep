// App.tsx
import React, { useEffect } from "react";
import { NavigationContainer } from "@react-navigation/native";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import OriginalsScreen from "@/screens/OriginalsScreen";
import RedactedScreen from "@/screens/RedactedScreen";
import * as ImagePicker from "expo-image-picker";
import { ensureDirs, saveToOriginals, saveToRedactedFromUri } from "@/storage/paths";
import { StatusBar } from "expo-status-bar";
import { MaterialIcons } from "@expo/vector-icons";
import { View, Alert, TouchableOpacity, Text, StyleSheet } from "react-native";
import { GalleryProvider } from "src/gallery/GalleryContext";
import { sendImageForRedaction } from "@/api/redact";
import { RequireAuth } from "src/auth/RequireAuth";
import { AuthProvider } from "src/auth/AuthContext";
import { InspectorProvider } from "src/inspect/InspectorContext";
import { ImageInspector } from "src/inspect/ImageInspector";

const Tab = createBottomTabNavigator();

export default function App() {
  useEffect(() => {
    ensureDirs();
  }, []);

  async function handleUpload() {
    const perm = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!perm.granted) {
      Alert.alert("Permission required", "Media library access is required to pick images.");
      return;
    }

    const res = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 1
    });
    if (res.canceled || res.assets.length === 0) return;

    try {
      const asset = res.assets[0];

      // Save original
      const savedOriginal = await saveToOriginals(asset.uri);

      // Send to API, get back a local URI we can display or persist
      const { uri: redactedTempUri, applied } = await sendImageForRedaction(savedOriginal);

      // Persist redacted file into your redacted folder
      const name = `redacted_${Date.now()}.jpg`;
      await saveToRedactedFromUri(redactedTempUri, name);

      Alert.alert("Done", applied ? "Redactions applied." : "No redactions found, saved original.");
    } catch (e: any) {
      Alert.alert("Processing failed", e.message ?? String(e));
    }
  }

  return (
    <AuthProvider>
      <GalleryProvider>
        <InspectorProvider>
            <NavigationContainer>
              <StatusBar style="auto" />
              <View style={{ flex: 1 }}>
                <Tab.Navigator
                  screenOptions={({ route }) => ({
                    tabBarIcon: ({ color, size }) => (
                      <MaterialIcons
                        name={route.name === "Redacted" ? "blur-on" : "photo-library"}
                        size={size}
                        color={color}
                      />
                    )
                  })}
                >
                  <Tab.Screen name="Redacted" component={RedactedScreen} />

                  {/* Originals locked behind RequireAuth */}
                  <Tab.Screen name="Originals" options={{ headerTitle: "Originals, locked" }}>
                    {() => (
                      <RequireAuth reason="Unlock Originals">
                        <OriginalsScreen />
                      </RequireAuth>
                    )}
                  </Tab.Screen>
                </Tab.Navigator>
              </View>
            </NavigationContainer>
          <ImageInspector />
        </InspectorProvider>
      </GalleryProvider>
    </AuthProvider>
  );
}
