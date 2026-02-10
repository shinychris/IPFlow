import { cn } from "@/lib/utils";
import { Check } from "lucide-react";
import { getWizardSteps, type ProjectType } from "@shared/schema";

interface StepIndicatorProps {
  currentStep: number;
  projectType: ProjectType;
  onStepClick?: (step: number) => void;
  className?: string;
}

export function StepIndicator({ currentStep, projectType, onStepClick, className }: StepIndicatorProps) {
  const steps = getWizardSteps(projectType);

  return (
    <div className={cn("flex items-center justify-between", className)}>
      {steps.map((step, index) => {
        const isCompleted = currentStep > step.id;
        const isCurrent = currentStep === step.id;
        const isLast = index === steps.length - 1;
        const isClickable = isCompleted || isCurrent || step.id === currentStep + 1;

        return (
          <div key={step.id} className="flex items-center flex-1">
            <div 
              className={cn(
                "flex flex-col items-center",
                isClickable && onStepClick && "cursor-pointer"
              )}
              onClick={() => isClickable && onStepClick?.(step.id)}
            >
              <div
                className={cn(
                  "flex h-10 w-10 items-center justify-center rounded-full border-2 transition-colors",
                  isCompleted && "border-primary bg-primary text-primary-foreground",
                  isCurrent && "border-primary bg-background text-primary",
                  !isCompleted && !isCurrent && "border-muted bg-muted text-muted-foreground",
                  isClickable && onStepClick && "hover:scale-105 transition-transform"
                )}
                data-testid={`step-indicator-${step.id}`}
              >
                {isCompleted ? (
                  <Check className="h-5 w-5" />
                ) : (
                  <span className="text-sm font-medium">{step.id}</span>
                )}
              </div>
              <div className="mt-2 flex flex-col items-center">
                <span
                  className={cn(
                    "text-sm font-medium",
                    (isCompleted || isCurrent) ? "text-foreground" : "text-muted-foreground"
                  )}
                >
                  {step.name}
                </span>
                <span className="text-xs text-muted-foreground hidden sm:block">
                  {step.description}
                </span>
              </div>
            </div>

            {!isLast && (
              <div
                className={cn(
                  "flex-1 h-0.5 mx-4 mt-[-24px]",
                  isCompleted ? "bg-primary" : "bg-muted"
                )}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
