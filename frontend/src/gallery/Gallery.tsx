import React from "react";
import {
  FlatList,
  Image,
  Pressable,
  StyleSheet,
  View,
  RefreshControl
} from "react-native";

type Props = {
  uris: string[];
  onPress?: (index: number) => void;
};

export function Gallery({
  uris,
  refreshing,
  onRefresh,
  onPress
}: {
  uris: string[];
  refreshing?: boolean;
  onRefresh?: () => void;
  onPress?: (index: number) => void;
}) {
  return (
    <FlatList
      data={uris}
      extraData={uris.length}
      keyExtractor={(item, i) => `${item}-${i}`}   // file:// duplicates are a thing
      numColumns={3}
      contentContainerStyle={{ padding: 8 }}
      columnWrapperStyle={{ gap: 8 }}
      renderItem={({ item, index }) => (
        <Pressable
          style={styles.cell}
          onPress={() => onPress?.(index)}
          android_ripple={{ color: "#00000022" }}
        >
          <Image source={{ uri: item }} style={styles.img} resizeMode="cover" />
        </Pressable>
      )}
      ItemSeparatorComponent={() => <View style={{ height: 8 }} />}
      refreshControl={
        onRefresh
          ? <RefreshControl refreshing={!!refreshing} onRefresh={onRefresh} />
          : undefined
      }
    />
  );
}

const styles = StyleSheet.create({
  cell: { flex: 1, aspectRatio: 1 },
  img: { flex: 1, borderRadius: 8 }
});
