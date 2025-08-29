import React, { useEffect } from "react";
import { NavigationContainer } from "@react-navigation/native";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import OriginalsScreen from "@/screens/OriginalsScreen";
import RedactedScreen from "@/screens/RedactedScreen";
import { UploadFab } from "@/components/UploadFab";
import * as ImagePicker from "expo-image-picker";
import { ensureDirs, saveToOriginals, saveToRedacted } from "@/storage/paths";
import { sendImageForRedaction } from "@/api/client";
import { StatusBar } from "expo-status-bar";
import { MaterialIcons } from "@expo/vector-icons";
import { View, Alert } from "react-native";
import { GalleryProvider } from "@/context/GalleryContext";

const Tab = createBottomTabNavigator();

export default function App() {
  useEffect(() => { ensureDirs(); }, []);

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
      const savedOriginal = await saveToOriginals(asset.uri);
      const bytes = await sendImageForRedaction(savedOriginal);
      const name = `redacted_${Date.now()}.jpg`;
      await saveToRedacted(bytes, name);
      Alert.alert("Done", "Redacted image saved.");
    } catch (e: any) {
      Alert.alert("Processing failed", e.message);
    }
  }

  return (
    <GalleryProvider>
      <NavigationContainer>
        <StatusBar style="auto" />
        <View style={{ flex: 1 }}>
          <Tab.Navigator screenOptions={({ route }) => ({
            headerRight: () => <UploadFab onPress={handleUpload} />,
            tabBarIcon: ({ color, size }) => (
              <MaterialIcons name={route.name === "Redacted" ? "blur-on" : "photo-library"} size={size} color={color} />
            )
          })}>
            <Tab.Screen name="Redacted" component={RedactedScreen} />
            <Tab.Screen name="Originals" component={OriginalsScreen} />
          </Tab.Navigator>
        </View>
      </NavigationContainer>
    </GalleryProvider>
  );
}