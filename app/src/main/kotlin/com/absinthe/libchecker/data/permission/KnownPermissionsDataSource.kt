package com.absinthe.libchecker.data.permission

import android.content.Context
import org.json.JSONObject

/**
 * Bundled fallback permission metadata.
 *
 * The system can only resolve labels/descriptions for permissions whose
 * defining package (`<permission>`) is currently installed. This data source
 * provides metadata extracted from real device dumps for well-known
 * permissions, so statistics and detail pages can still show a label and the
 * defining package when the system lookup fails.
 */
class KnownPermissionsDataSource(private val context: Context) {

  data class KnownPermission(
    val label: String?,
    val description: String?,
    val source: String?,
    val protectionLevel: String?
  )

  private val permissions: Map<String, KnownPermission> by lazy(LazyThreadSafetyMode.SYNCHRONIZED) {
    runCatching {
      context.assets.open(ASSET_PATH).bufferedReader().use { reader ->
        val root = JSONObject(reader.readText())
        val obj = root.getJSONObject("permissions")
        buildMap {
          val keys = obj.keys()
          while (keys.hasNext()) {
            val name = keys.next()
            val item = obj.getJSONObject(name)
            put(
              name,
              KnownPermission(
                label = item.optString("label").takeIf { it.isNotBlank() },
                description = item.optString("description").takeIf { it.isNotBlank() },
                source = item.optString("source").takeIf { it.isNotBlank() },
                protectionLevel = item.optString("protectionLevel").takeIf { it.isNotBlank() }
              )
            )
          }
        }
      }
    }.getOrDefault(emptyMap())
  }

  fun get(permissionName: String): KnownPermission? = permissions[permissionName]

  private companion object {
    const val ASSET_PATH = "permissions/known_permissions.json"
  }
}
