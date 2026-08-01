package com.absinthe.libchecker.data.statistics

import android.content.pm.PackageManager
import com.absinthe.libchecker.data.permission.KnownPermissionsDataSource
import com.absinthe.libchecker.domain.statistics.reference.repository.PermissionLabelResolver
import java.util.Collections

class AndroidPermissionLabelResolver(
  private val packageManager: PackageManager,
  private val knownPermissionsDataSource: KnownPermissionsDataSource
) : PermissionLabelResolver {

  // Memoized: resolve() is called per statistics item on a background thread,
  // each system lookup is a binder IPC. Nulls are cached too (unknown permissions).
  private val cache = Collections.synchronizedMap(mutableMapOf<String, String?>())

  override fun resolve(permissionName: String): String? {
    val normalizedName = permissionName.substringBefore(" ")
    return cache.getOrPut(normalizedName) {
      resolveFromSystem(normalizedName)
        ?: knownPermissionsDataSource.get(normalizedName)?.label
    }
  }

  private fun resolveFromSystem(permissionName: String): String? {
    return runCatching {
      packageManager
        .getPermissionInfo(permissionName, 0)
        .loadLabel(packageManager)
        .toString()
        .takeIf { it.isNotBlank() && it != permissionName }
    }.getOrNull()
  }
}
