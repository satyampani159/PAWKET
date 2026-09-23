import React, { useEffect, useRef } from 'react';

import { Animated } from 'react-native';

import Svg, {
  Path,
} from 'react-native-svg';

const AnimatedPath =
  Animated.createAnimatedComponent(Path);

export default function DogTraceLogo() {
  const progress = useRef(
    new Animated.Value(1)
  ).current;

  useEffect(() => {
    Animated.timing(progress, {
      toValue: 0,
      duration: 2200,
      useNativeDriver: false,
    }).start();
  }, []);

  const strokeDashoffset =
    progress.interpolate({
      inputRange: [0, 1],
      outputRange: [0, 1500],
    });

  return (
    <Svg
      width={190}
      height={190}
      viewBox="0 0 512 512"
    >
      <AnimatedPath
        d="M256 40C150 40 72 118 72 224c0 86 55 160 132 188l52 60 52-60c77-28 132-102 132-188C440 118 362 40 256 40z"
        fill="none"
        stroke="#FFFFFF"
        strokeWidth={8}
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeDasharray="1500"
        strokeDashoffset={
          strokeDashoffset
        }
      />
    </Svg>
  );
}