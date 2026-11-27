package com.businessai.fieldservice

import platform.Foundation.NSDate
import platform.Foundation.NSUUID

actual fun platformName(): String = "iOS (UI later)"

actual fun randomUuid(): String = NSUUID().UUIDString.lowercase()

actual fun currentTimeIso(): String {
    // Coarse ISO-ish stamp for offline queue metadata (iOS UI is out of M5 scope).
    val seconds = NSDate().timeIntervalSince1970.toLong()
    return "${seconds}.000Z"
}
