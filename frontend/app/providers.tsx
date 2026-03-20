"use client";

import { QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider } from "@/components/theme-provider";
import { TooltipProvider } from "@/components/ui/tooltip";
import { useState } from "react";
import { createQueryClient } from "@/lib/queryClient";

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => createQueryClient());

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider defaultTheme="light" storageKey="ip-kit-theme">
        <TooltipProvider>
          {children}
        </TooltipProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}
