import React, { useState } from "react";
import { Modal, View, Text, TextInput, Pressable } from "react-native";

export const PinModal: React.FC<{
  visible: boolean;
  onSubmit: (pin: string) => void;
  onCancel: () => void;
}> = ({ visible, onSubmit, onCancel }) => {
  const [pin, setPin] = useState("");
  return (
    <Modal transparent visible={visible} animationType="fade" onRequestClose={onCancel}>
      <View style={{ flex: 1, backgroundColor: "rgba(0,0,0,0.4)", justifyContent: "center", alignItems: "center" }}>
        <View style={{ width: 300, backgroundColor: "white", borderRadius: 12, padding: 16 }}>
          <Text style={{ fontSize: 18, fontWeight: "700", marginBottom: 8 }}>Enter PIN</Text>
          <TextInput
            value={pin}
            onChangeText={setPin}
            placeholder="4 to 8 digits"
            secureTextEntry
            keyboardType="number-pad"
            style={{ borderWidth: 1, borderColor: "#ccc", borderRadius: 8, padding: 10, marginBottom: 12 }}
          />
          <View style={{ flexDirection: "row", justifyContent: "flex-end", gap: 12 }}>
            <Pressable onPress={onCancel} style={{ padding: 10 }}>
              <Text>Cancel</Text>
            </Pressable>
            <Pressable
              onPress={() => { onSubmit(pin); setPin(""); }}
              style={{ backgroundColor: "#111", paddingVertical: 10, paddingHorizontal: 16, borderRadius: 8 }}
            >
              <Text style={{ color: "white" }}>Unlock</Text>
            </Pressable>
          </View>
        </View>
      </View>
    </Modal>
  );
};
