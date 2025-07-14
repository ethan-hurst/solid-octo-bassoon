/**
 * Crash Reporting Service - Comprehensive error tracking and crash reporting
 */
import { Platform } from 'react-native';
import crashlytics from '@react-native-firebase/crashlytics';
import { setJSExceptionHandler, setNativeExceptionHandler } from 'react-native-exception-handler';

export interface CrashReport {
  error: Error;
  isFatal: boolean;
  userId?: string;
  metadata?: Record<string, any>;
  breadcrumbs?: string[];
}

export interface ErrorContext {
  screen?: string;
  action?: string;
  userId?: string;
  additionalData?: Record<string, any>;
}

class CrashReportingService {
  private isInitialized = false;
  private userId: string | null = null;
  private breadcrumbs: string[] = [];
  private maxBreadcrumbs = 50;

  async initialize(): Promise<void> {
    if (this.isInitialized) return;

    try {
      // Initialize Firebase Crashlytics
      await crashlytics().setCrashlyticsCollectionEnabled(true);
      
      // Set up JS exception handler
      this.setupJSExceptionHandler();
      
      // Set up native exception handler
      this.setupNativeExceptionHandler();
      
      this.isInitialized = true;
      console.log('Crash reporting service initialized');
    } catch (error) {
      console.error('Failed to initialize crash reporting:', error);
    }
  }

  private setupJSExceptionHandler(): void {
    setJSExceptionHandler((error, isFatal) => {
      this.reportCrash({
        error,
        isFatal,
        userId: this.userId || undefined,
        metadata: {
          platform: Platform.OS,
          breadcrumbs: this.breadcrumbs,
        },
        breadcrumbs: this.breadcrumbs,
      });
    }, true);
  }

  private setupNativeExceptionHandler(): void {
    setNativeExceptionHandler((exceptionString) => {
      const error = new Error(exceptionString);
      this.reportCrash({
        error,
        isFatal: true,
        userId: this.userId || undefined,
        metadata: {
          platform: Platform.OS,
          type: 'native',
          breadcrumbs: this.breadcrumbs,
        },
        breadcrumbs: this.breadcrumbs,
      });
    });
  }

  setUserId(userId: string): void {
    this.userId = userId;
    if (this.isInitialized) {
      crashlytics().setUserId(userId);
    }
  }

  clearUserId(): void {
    this.userId = null;
    if (this.isInitialized) {
      crashlytics().setUserId('');
    }
  }

  setUserAttribute(key: string, value: string): void {
    if (this.isInitialized) {
      crashlytics().setCustomAttribute(key, value);
    }
  }

  addBreadcrumb(message: string, category?: string): void {
    const timestamp = new Date().toISOString();
    const breadcrumb = category ? `[${category}] ${message}` : message;
    const timestampedBreadcrumb = `${timestamp}: ${breadcrumb}`;
    
    this.breadcrumbs.push(timestampedBreadcrumb);
    
    // Keep only the most recent breadcrumbs
    if (this.breadcrumbs.length > this.maxBreadcrumbs) {
      this.breadcrumbs = this.breadcrumbs.slice(-this.maxBreadcrumbs);
    }

    if (this.isInitialized) {
      crashlytics().log(timestampedBreadcrumb);
    }
  }

  reportError(error: Error, context?: ErrorContext): void {
    this.addBreadcrumb(`Error occurred: ${error.message}`, 'error');
    
    if (this.isInitialized) {
      // Set context attributes
      if (context) {
        if (context.screen) {
          crashlytics().setCustomAttribute('screen', context.screen);
        }
        if (context.action) {
          crashlytics().setCustomAttribute('action', context.action);
        }
        if (context.userId) {
          crashlytics().setUserId(context.userId);
        }
        if (context.additionalData) {
          Object.entries(context.additionalData).forEach(([key, value]) => {
            crashlytics().setCustomAttribute(key, String(value));
          });
        }
      }

      // Record the error
      crashlytics().recordError(error);
    }
  }

  reportCrash(report: CrashReport): void {
    console.error('App Crash Detected:', {
      error: report.error.message,
      stack: report.error.stack,
      isFatal: report.isFatal,
      userId: report.userId,
      metadata: report.metadata,
    });

    if (this.isInitialized) {
      // Set crash metadata
      if (report.userId) {
        crashlytics().setUserId(report.userId);
      }

      if (report.metadata) {
        Object.entries(report.metadata).forEach(([key, value]) => {
          crashlytics().setCustomAttribute(key, String(value));
        });
      }

      // Add breadcrumbs as logs
      if (report.breadcrumbs) {
        report.breadcrumbs.forEach(breadcrumb => {
          crashlytics().log(breadcrumb);
        });
      }

      // Record the crash
      if (report.isFatal) {
        crashlytics().crash();
      } else {
        crashlytics().recordError(report.error);
      }
    }
  }

  async checkForUnsentReports(): Promise<boolean> {
    if (!this.isInitialized) return false;
    
    try {
      return await crashlytics().checkForUnsentReports();
    } catch (error) {
      console.error('Failed to check for unsent reports:', error);
      return false;
    }
  }

  async sendUnsentReports(): Promise<void> {
    if (!this.isInitialized) return;
    
    try {
      await crashlytics().sendUnsentReports();
    } catch (error) {
      console.error('Failed to send unsent reports:', error);
    }
  }

  async deleteUnsentReports(): Promise<void> {
    if (!this.isInitialized) return;
    
    try {
      await crashlytics().deleteUnsentReports();
    } catch (error) {
      console.error('Failed to delete unsent reports:', error);
    }
  }

  // Convenience methods for common scenarios
  reportNetworkError(error: Error, url: string, method: string): void {
    this.reportError(error, {
      action: 'network_request',
      additionalData: {
        url,
        method,
        error_type: 'network',
      },
    });
  }

  reportAuthenticationError(error: Error, authMethod: string): void {
    this.reportError(error, {
      action: 'authentication',
      additionalData: {
        auth_method: authMethod,
        error_type: 'authentication',
      },
    });
  }

  reportBettingError(error: Error, betType: string, amount?: number): void {
    this.reportError(error, {
      action: 'betting',
      additionalData: {
        bet_type: betType,
        bet_amount: amount,
        error_type: 'betting',
      },
    });
  }

  reportUIError(error: Error, component: string, props?: Record<string, any>): void {
    this.reportError(error, {
      action: 'ui_interaction',
      additionalData: {
        component,
        props: props ? JSON.stringify(props) : undefined,
        error_type: 'ui',
      },
    });
  }

  reportDataError(error: Error, dataType: string, operation: string): void {
    this.reportError(error, {
      action: 'data_operation',
      additionalData: {
        data_type: dataType,
        operation,
        error_type: 'data',
      },
    });
  }

  // Test crash (for development only)
  testCrash(): void {
    if (__DEV__) {
      crashlytics().crash();
    }
  }
}

export const crashReportingService = new CrashReportingService();