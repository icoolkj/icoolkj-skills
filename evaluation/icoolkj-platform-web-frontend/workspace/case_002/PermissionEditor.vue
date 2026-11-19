<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

type Role = { id: string; name: string }
type Permission = { code: string; name: string }
type Api = {
  getRolePermissions(roleId: string): Promise<{ codes: string[] }>
  updateRolePermissions(roleId: string, codes: string[]): Promise<{ codes: string[] }>
}

const props = defineProps<{ roles: Role[]; api: Api; availablePermissions: Permission[]; initialRoleId: string }>()
const selectedRoleId = ref(props.initialRoleId)
const selectedCodes = ref<string[]>([])
const saving = ref(false)

function changeRole(roleId: string) {
  selectedRoleId.value = roleId
  selectedCodes.value = []
}

async function savePermissions() {
  saving.value = true
  const result = await props.api.updateRolePermissions(selectedRoleId.value, selectedCodes.value)
  selectedCodes.value = result.codes
  ElMessage.success('权限已保存')
  saving.value = false
}
</script>

<template>
  <el-select v-model="selectedRoleId" @change="changeRole">
    <el-option v-for="role in roles" :key="role.id" :label="role.name" :value="role.id" />
  </el-select>
  <el-checkbox-group v-model="selectedCodes">
    <el-checkbox v-for="permission in availablePermissions" :key="permission.code" :value="permission.code">
      {{ permission.name }}
    </el-checkbox>
  </el-checkbox-group>
  <el-button type="primary" :loading="saving" @click="savePermissions">保存权限</el-button>
</template>
