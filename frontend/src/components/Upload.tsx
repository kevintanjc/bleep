import React from "react";
import { Pressable, StyleSheet, View } from "react-native";
import { MaterialIcons } from "@expo/vector-icons";

export function UploadButton({ onPress }: { onPress: () => void }) {
  return (
    <View style={styles.wrap}>
      <Pressable accessibilityRole="button" onPress={onPress} style={styles.fab}>
        <MaterialIcons name="add" size={28} color="#fff" />
      </Pressable>
    </View>
  );
}


const styles = StyleSheet.create({
  wrap: { position: "absolute", right: 16, bottom: 16 },
  fab: {
    width: 56,
    height: 56,
    borderRadius: 28,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "white",
    elevation: 4
  }
});