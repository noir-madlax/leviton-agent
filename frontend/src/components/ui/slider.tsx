"use client"

import * as React from "react"
import { cn } from "@/lib/utils"

interface SliderProps extends React.HTMLAttributes<HTMLDivElement> {
  value: number[]
  onValueChange: (value: number[]) => void
  min?: number
  max?: number
  step?: number
  disabled?: boolean
}

const Slider = React.forwardRef<HTMLDivElement, SliderProps>(
  ({ className, value, onValueChange, min = 0, max = 100, step = 1, disabled = false, ...props }, ref) => {
    const handleChange = (index: number, newValue: number) => {
      const newValues = [...value]
      newValues[index] = newValue
      onValueChange(newValues)
    }

    return (
      <div
        ref={ref}
        className={cn(
          "relative flex w-full touch-none select-none items-center",
          className
        )}
        {...props}
      >
        <div className="relative h-2 w-full grow overflow-hidden rounded-full bg-secondary">
          <div 
            className="absolute h-full bg-primary"
            style={{
              left: `${((value[0] - min) / (max - min)) * 100}%`,
              width: `${((value[1] - value[0]) / (max - min)) * 100}%`
            }}
          />
        </div>
        
        {/* Min handle */}
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={value[0]}
          disabled={disabled}
          onChange={(e) => handleChange(0, Number(e.target.value))}
          className="absolute inset-0 h-2 w-full cursor-pointer opacity-0"
        />
        
        {/* Max handle */}
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={value[1]}
          disabled={disabled}
          onChange={(e) => handleChange(1, Number(e.target.value))}
          className="absolute inset-0 h-2 w-full cursor-pointer opacity-0"
        />
        
        {/* Visual handles */}
        <div 
          className="absolute h-4 w-4 rounded-full border-2 border-primary bg-background ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50"
          style={{ left: `${((value[0] - min) / (max - min)) * 100}%`, transform: 'translateX(-50%)' }}
        />
        <div 
          className="absolute h-4 w-4 rounded-full border-2 border-primary bg-background ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50"
          style={{ left: `${((value[1] - min) / (max - min)) * 100}%`, transform: 'translateX(-50%)' }}
        />
      </div>
    )
  }
)

Slider.displayName = "Slider"

export { Slider } 