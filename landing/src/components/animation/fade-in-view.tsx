"use client";

import { motion, type Variants } from "motion/react";
import type { ReactNode } from "react";

interface FadeInViewProps {
  children: ReactNode;
  className?: string;
  delay?: number;
  duration?: number;
  direction?: "up" | "down" | "left" | "right";
  distance?: number;
  once?: boolean;
  amount?: number;
}

const getInitialPosition = (direction: string, distance: number) => {
  switch (direction) {
    case "up":
      return { y: distance };
    case "down":
      return { y: -distance };
    case "left":
      return { x: distance };
    case "right":
      return { x: -distance };
    default:
      return { y: distance };
  }
};

export function FadeInView({
  children,
  className,
  delay = 0,
  duration = 0.5,
  direction = "up",
  distance = 24,
  once = true,
  amount = 0.3,
}: FadeInViewProps) {
  const initial = {
    opacity: 0,
    ...getInitialPosition(direction, distance),
  };

  const animate = {
    opacity: 1,
    x: 0,
    y: 0,
  };

  return (
    <motion.div
      className={className}
      initial={initial}
      whileInView={animate}
      viewport={{ once, amount }}
      transition={{
        duration,
        delay,
        ease: [0.25, 0.1, 0.25, 1], // cubic-bezier for smooth easing
      }}
    >
      {children}
    </motion.div>
  );
}

// Stagger container for children animations
interface StaggerContainerProps {
  children: ReactNode;
  className?: string;
  staggerDelay?: number;
  once?: boolean;
  amount?: number;
}

export function StaggerContainer({
  children,
  className,
  staggerDelay = 0.1,
  once = true,
  amount = 0.2,
}: StaggerContainerProps) {
  const containerVariants: Variants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: staggerDelay,
      },
    },
  };

  return (
    <motion.div
      className={className}
      variants={containerVariants}
      initial="hidden"
      whileInView="visible"
      viewport={{ once, amount }}
    >
      {children}
    </motion.div>
  );
}

// Stagger item for use inside StaggerContainer
interface StaggerItemProps {
  children: ReactNode;
  className?: string;
  direction?: "up" | "down" | "left" | "right";
  distance?: number;
  duration?: number;
}

export function StaggerItem({
  children,
  className,
  direction = "up",
  distance = 24,
  duration = 0.5,
}: StaggerItemProps) {
  const getInitial = () => {
    switch (direction) {
      case "up":
        return { opacity: 0, y: distance };
      case "down":
        return { opacity: 0, y: -distance };
      case "left":
        return { opacity: 0, x: distance };
      case "right":
        return { opacity: 0, x: -distance };
      default:
        return { opacity: 0, y: distance };
    }
  };

  const itemVariants: Variants = {
    hidden: getInitial(),
    visible: {
      opacity: 1,
      x: 0,
      y: 0,
      transition: {
        duration,
        ease: [0.25, 0.1, 0.25, 1],
      },
    },
  };

  return (
    <motion.div className={className} variants={itemVariants}>
      {children}
    </motion.div>
  );
}
