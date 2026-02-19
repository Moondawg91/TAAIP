/// <reference types="react" />
/// <reference types="vite/client" />

// Provide basic fallback for JSX IntrinsicElements when tooling is strict
declare global {
  namespace JSX {
    interface IntrinsicElements {
      [elemName: string]: any;
    }
  }
}

export {};
