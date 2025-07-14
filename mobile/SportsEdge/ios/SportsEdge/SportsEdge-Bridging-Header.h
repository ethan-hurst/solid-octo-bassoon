//
//  SportsEdge-Bridging-Header.h
//  SportsEdge
//
//  Created by React Native
//

#ifndef SportsEdge_Bridging_Header_h
#define SportsEdge_Bridging_Header_h

#import <React/RCTBridgeModule.h>
#import <React/RCTViewManager.h>
#import <React/RCTUIManager.h>
#import <React/RCTUtils.h>
#import <React/RCTDevSettings.h>

// Firebase imports
#if __has_include(<Firebase/Firebase.h>)
#import <Firebase/Firebase.h>
#endif

// Local Authentication
#if __has_include(<LocalAuthentication/LocalAuthentication.h>)
#import <LocalAuthentication/LocalAuthentication.h>
#endif

// UserNotifications
#if __has_include(<UserNotifications/UserNotifications.h>)
#import <UserNotifications/UserNotifications.h>
#endif

#endif /* SportsEdge_Bridging_Header_h */