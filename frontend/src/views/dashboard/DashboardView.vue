<template>
  <div>
    <el-row :gutter="16">
      <el-col :span="6" v-for="card in visibleCards" :key="card.title">
        <el-card shadow="hover">
          <div style="display:flex;align-items:center;gap:12px">
            <el-icon :size="32" :color="card.color"><component :is="card.icon" /></el-icon>
            <div>
              <div style="font-size:13px;color:#909399">{{ card.title }}</div>
              <div style="font-size:24px;font-weight:bold">
                <span v-if="loading">--</span>
                <span v-else>{{ card.key === 'unpaid_amount' ? card.value.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : card.value }}</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <div style="margin-top:12px;text-align:right">
      <el-button size="small" link type="primary" @click="showUnpaid = !showUnpaid">
        {{ showUnpaid ? '隐藏未收款' : '显示未收款' }}
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import request from '@/api/request'

const loading = ref(true)
const showUnpaid = ref(false)

const cards = ref([
  { title: '本月新增线索', icon: 'TrendCharts', color: '#409eff', value: 0, key: 'monthly_leads', sensitive: false },
  { title: '在服务客户数', icon: 'OfficeBuilding', color: '#67c23a', value: 0, key: 'active_customers', sensitive: false },
  { title: '本月新签合同', icon: 'Document', color: '#e6a23c', value: 0, key: 'monthly_contracts', sensitive: false },
  { title: '待执行任务', icon: 'Calendar', color: '#f56c6c', value: 0, key: 'pending_tasks', sensitive: false },
  { title: '未收款金额(元)', icon: 'Money', color: '#909399', value: 0, key: 'unpaid_amount', sensitive: true },
])

const visibleCards = computed(() =>
  cards.value.filter(c => !c.sensitive || showUnpaid.value)
)

onMounted(async () => {
  try {
    const data = await request.get<Record<string, number>>('/dashboard/stats')
    cards.value.forEach(card => {
      card.value = (data as unknown as Record<string, number>)[card.key] ?? 0
    })
  } finally {
    loading.value = false
  }
})
</script>
