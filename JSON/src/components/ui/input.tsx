import * as React from "react";

import { cn } from "@/lib/utils";

const Input = React.forwardRef<HTMLInputElement, React.ComponentProps<"input">>(
  ({ className, type, onChange, onInput, ...props }, ref) => {
    const transformToUppercase = (
      event: React.FormEvent<HTMLInputElement> | React.ChangeEvent<HTMLInputElement>
    ) => {
      const input = event.currentTarget;
      const { selectionStart, selectionEnd } = input;
      const uppercasedValue = input.value.toUpperCase();

      if (input.value !== uppercasedValue) {
        input.value = uppercasedValue;
        if (selectionStart !== null && selectionEnd !== null) {
          input.setSelectionRange(selectionStart, selectionEnd);
        }
      }
    };

    const handleInput = (event: React.FormEvent<HTMLInputElement>) => {
      transformToUppercase(event);
      onInput?.(event);
    };

    const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
      transformToUppercase(event);
      onChange?.(event);
    };

    return (
      <input
        type={type}
        className={cn(
          "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-base uppercase ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-foreground placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 md:text-sm",
          className,
        )}
        ref={ref}
        onInput={handleInput}
        onChange={handleChange}
        {...props}
      />
    );
  },
);
Input.displayName = "Input";

export { Input };
