import { useEffect, useRef, useState } from 'react'
import { animate } from 'motion'

/** 숫자를 현재 값에서 목표 값까지 스프링감 있게 카운트업한다. reduced-motion이면 즉시 반영. */
export function useCountUp(target: number, duration = 0.9) {
  const [value, setValue] = useState(0)
  const prev = useRef(0)

  useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      prev.current = target
      setValue(target)
      return
    }
    const controls = animate(prev.current, target, {
      duration,
      ease: [0.22, 0.8, 0.3, 1],
      onUpdate: v => setValue(Math.round(v)),
    })
    prev.current = target
    return () => controls.stop()
  }, [target, duration])

  return value
}
