import React from "react";
import {
  FlatList,
  Image,
  Pressable,
  StyleSheet,
  View,
  RefreshControl
} from "react-native";

export function Gallery({
  uris,
  refreshing,
  onRefresh
}: {
  uris: string[];
  refreshing?: boolean;
  onRefresh?: () => void;
}) {
  return (
    <FlatList
      data={uris}
      extraData={uris.length}
      keyExtractor={item => item}
      numColumns={3}
      contentContainerStyle={{ padding: 8 }}
      columnWrapperStyle={{ gap: 8 }}
      renderItem={({ item }) => (
        <Pressable style={styles.cell}>
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
