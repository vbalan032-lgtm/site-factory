import { Button as BaseButton } from "@base-ui/react/button";
import type { ComponentProps } from "react";

export function Button(props: ComponentProps<typeof BaseButton>) {
  return <BaseButton {...props} />;
}

