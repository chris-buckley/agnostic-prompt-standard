/**
 * A discriminated union representing either a successful value or an error.
 * Use this pattern to make error handling explicit and avoid throwing exceptions
 * for recoverable errors.
 */
export type Result<T, E = Error> = { ok: true; value: T } | { ok: false; error: E };

/**
 * Creates a successful Result containing the given value.
 * @param value - The success value to wrap.
 * @returns A Result indicating success.
 */
export function ok<T>(value: T): Result<T, never> {
  return { ok: true, value };
}

/**
 * Creates a failed Result containing the given error.
 * @param error - The error to wrap.
 * @returns A Result indicating failure.
 */
export function err<E>(error: E): Result<never, E> {
  return { ok: false, error };
}

/**
 * Type guard to check if a Result is successful.
 * @param result - The Result to check.
 * @returns True if the Result is successful.
 */
export function isOk<T, E>(result: Result<T, E>): result is { ok: true; value: T } {
  return result.ok;
}

/**
 * Type guard to check if a Result is an error.
 * @param result - The Result to check.
 * @returns True if the Result is an error.
 */
export function isErr<T, E>(result: Result<T, E>): result is { ok: false; error: E } {
  return !result.ok;
}

/**
 * Unwraps a Result, returning the value if successful or throwing the error.
 * @param result - The Result to unwrap.
 * @returns The success value.
 * @throws The error if the Result is a failure.
 */
export function unwrap<T, E>(result: Result<T, E>): T {
  if (result.ok) return result.value;
  if (result.error instanceof Error) throw result.error;
  throw new Error(String(result.error));
}

/**
 * Unwraps a Result, returning the value if successful or a default value.
 * @param result - The Result to unwrap.
 * @param defaultValue - The value to return if the Result is an error.
 * @returns The success value or the default value.
 */
export function unwrapOr<T, E>(result: Result<T, E>, defaultValue: T): T {
  return result.ok ? result.value : defaultValue;
}
