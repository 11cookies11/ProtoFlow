export function withResult<T>(value: T | Promise<T>, handler: (payload: T) => void) {
  if (value && typeof (value as any).then === 'function') {
    ;(value as Promise<T>).then(handler)
    return
  }
  handler(value as T)
}
