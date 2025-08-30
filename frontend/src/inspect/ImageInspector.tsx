import React from "react";
import ImageViewing from "react-native-image-viewing";
import { useInspector } from "./InspectorContext";

export const ImageInspector = () => {
  const { state, close } = useInspector();
  return (
    <ImageViewing
      images={state.items}
      imageIndex={state.index}
      visible={state.visible}
      onRequestClose={close}
      swipeToCloseEnabled
      doubleTapToZoomEnabled
    />
  );
};