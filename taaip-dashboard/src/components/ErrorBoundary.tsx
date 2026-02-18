import React from 'react';

type Props = {
  children: React.ReactNode;
  fallbackTitle?: string;
  fallbackMessage?: string;
};

type State = {
  hasError: boolean;
  error?: Error | null;
};

export class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // Basic logging; could be extended to send to a telemetry service
    // eslint-disable-next-line no-console
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  handleReload = () => {
    // Simple recovery: full page reload to reset app state
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
          <div className="max-w-lg w-full bg-white border border-gray-200 rounded-lg shadow-md p-6 text-center">
            <h2 className="text-xl font-semibold text-gray-900">
              {this.props.fallbackTitle || 'Something went wrong'}
            </h2>
            <p className="mt-2 text-gray-600">
              {this.props.fallbackMessage || 'We hit an unexpected error while rendering this view.'}
            </p>
            <p className="mt-2 text-xs text-gray-400 break-all">
              {this.state.error?.message}
            </p>
            <button
              onClick={this.handleReload}
              className="mt-4 inline-flex items-center px-4 py-2 rounded bg-yellow-500 text-black font-medium hover:bg-yellow-400"
            >
              Reload
            </button>
          </div>
        </div>
      );
    }
    return this.props.children as React.ReactElement;
  }
}

export default ErrorBoundary;
