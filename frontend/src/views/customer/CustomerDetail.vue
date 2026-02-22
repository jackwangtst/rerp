<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { customerApi, type CustomerDetail, type FollowUp } from '@/api/customer'

const route = useRoute()
const router = useRouter()
const customerId = route.params.id as string

const customer = ref<CustomerDetail | null>(null)
const followUps = ref<FollowUp[]>([])
const loading = ref(false)

// 跟进记录表单
const fuForm = ref({ follow_type: '电话', content: '', next_date: '' })
const fuSaving = ref(false)
const followTypeOptions = ['电话', '拜访', '邮件', '微信', '其他']

async function load() {
  loading.value = true
  try {
    const [cRes, fuRes] = await Promise.all([
      customerApi.get(customerId),
      customerApi.listFollowUps(customerId),
    ])
    customer.value = cRes.data
    followUps.value = fuRes.data
  } finally {
    loading.value = false
  }
}

async function addFollowUp() {
  if (!fuForm.value.content) { ElMessage.warning('请填写跟进内容'); return }
  fuSaving.value = true
  try {
    await customerApi.addFollowUp(customerId, { ...fuForm.value })
    ElMessage.success('已记录')
    fuForm.value = { follow_type: '电话', content: '', next_date: '' }
    const res = await customerApi.listFollowUps(customerId)
    followUps.value = res.data
  } finally {
    fuSaving.value = false
  }
}

onMounted(load)
</script>

<template>
  <div v-loading="loading">
    <el-page-header @back="router.back()" style="margin-bottom:16px">
      <template #content>
        <span>{{ customer?.company_name ?? '客户详情' }}</span>
      </template>
    </el-page-header>

    <el-row :gutter="16">
      <!-- 左侧：基本信息 + 联系人 -->
      <el-col :span="16">
        <el-card shadow="never" style="margin-bottom:16px">
          <template #header><span>基本信息</span></template>
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item label="客户编号">{{ customer?.customer_no }}</el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag size="small">{{ customer?.status }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="公司全称">{{ customer?.company_name }}</el-descriptions-item>
            <el-descriptions-item label="公司简称">{{ customer?.company_short_name }}</el-descriptions-item>
            <el-descriptions-item label="行业">{{ customer?.industry }}</el-descriptions-item>
            <el-descriptions-item label="规模">{{ customer?.company_size }}</el-descriptions-item>
            <el-descriptions-item label="省份">{{ customer?.province }}</el-descriptions-item>
            <el-descriptions-item label="城市">{{ customer?.city }}</el-descriptions-item>
            <el-descriptions-item label="法定代表人">{{ customer?.legal_representative }}</el-descriptions-item>
            <el-descriptions-item label="客户等级">{{ customer?.customer_level }}</el-descriptions-item>
            <el-descriptions-item label="统一信用代码" :span="2">{{ customer?.unified_social_credit_code }}</el-descriptions-item>
            <el-descriptions-item label="备注" :span="2">{{ customer?.remark }}</el-descriptions-item>
          </el-descriptions>
        </el-card>

        <el-card shadow="never">
          <template #header><span>联系人</span></template>
          <el-table :data="customer?.contacts ?? []" size="small">
            <el-table-column prop="name" label="姓名" width="100" />
            <el-table-column prop="title" label="职务" width="100" />
            <el-table-column prop="department" label="部门" width="120" />
            <el-table-column prop="phone" label="电话" width="130" />
            <el-table-column prop="email" label="邮箱" show-overflow-tooltip />
            <el-table-column prop="wechat" label="微信" width="110" />
            <el-table-column prop="is_primary" label="主要联系人" width="90" align="center">
              <template #default="{ row }">
                <el-tag v-if="row.is_primary" type="success" size="small">是</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <!-- 右侧：跟进记录 -->
      <el-col :span="8">
        <el-card shadow="never">
          <template #header><span>跟进记录</span></template>

          <!-- 新增跟进 -->
          <div style="margin-bottom:12px">
            <el-select v-model="fuForm.follow_type" size="small" style="width:80px;margin-right:6px">
              <el-option v-for="t in followTypeOptions" :key="t" :label="t" :value="t" />
            </el-select>
            <el-date-picker v-model="fuForm.next_date" type="date" placeholder="下次跟进" size="small"
              value-format="YYYY-MM-DD" style="width:130px" />
            <el-input v-model="fuForm.content" type="textarea" :rows="2" placeholder="跟进内容..."
              style="margin-top:6px" />
            <el-button type="primary" size="small" :loading="fuSaving" style="margin-top:6px;width:100%"
              @click="addFollowUp">记录跟进</el-button>
          </div>

          <el-divider style="margin:8px 0" />

          <!-- 历史记录 -->
          <el-timeline>
            <el-timeline-item
              v-for="fu in followUps"
              :key="fu.id"
              :timestamp="fu.created_at.slice(0, 16).replace('T', ' ')"
              placement="top"
            >
              <div style="font-size:12px">
                <el-tag size="small" style="margin-right:4px">{{ fu.follow_type }}</el-tag>
                {{ fu.content }}
                <div v-if="fu.next_date" style="color:#909399;margin-top:2px">
                  下次跟进：{{ fu.next_date }}
                </div>
              </div>
            </el-timeline-item>
            <div v-if="followUps.length === 0" style="color:#c0c4cc;text-align:center;padding:20px 0;font-size:13px">
              暂无跟进记录
            </div>
          </el-timeline>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>
