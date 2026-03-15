<script setup lang="ts">
import { ref, onMounted } from 'vue'
import request from '@/api/request'

interface MonthlySeries { month: number; received: number }
interface InvoiceStat { status: string; count: number; amount: number }
interface FinanceStats {
  total_contract: number
  total_received: number
  total_unpaid: number
  status_dist: Record<string, number>
  monthly_series: MonthlySeries[]
  invoice_stats: InvoiceStat[]
  year: number
}

const loading = ref(false)
const year = ref(new Date().getFullYear())
const stats = ref<FinanceStats | null>(null)

const MONTHS = ['1月','2月','3月','4月','5月','6月','7月','8月','9月','10月','11月','12月']

async function loadStats() {
  loading.value = true
  try {
    const data = await request.get<any, FinanceStats>('/dashboard/finance-stats', { params: { year: year.value } })
    stats.value = data
  } finally {
    loading.value = false
  }
}

function fmt(v: number) {
  return v.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function statusTagType(s: string) {
  if (s === '已收款') return 'success'
  if (s === '部分收款') return 'warning'
  return 'info'
}

function invoiceStatusType(s: string) {
  if (s === '已上传') return 'success'
  if (s === '已开具' || s === '已邮寄') return 'primary'
  return 'info'
}

// 月度柱状图：用 CSS 简单实现（不引入 echarts）
function barWidth(v: number) {
  if (!stats.value) return '0%'
  const max = Math.max(...stats.value.monthly_series.map(m => m.received), 1)
  return (v / max * 100).toFixed(1) + '%'
}

onMounted(() => loadStats())
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h2>财务统计</h2>
      <div style="display:flex;align-items:center;gap:8px">
        <span style="font-size:13px;color:#606266">年度：</span>
        <el-input-number v-model="year" :min="2020" :max="2099" :step="1" controls-position="right" style="width:110px" @change="loadStats" />
      </div>
    </div>

    <div v-loading="loading">
      <!-- 汇总卡片 -->
      <el-row :gutter="16" style="margin-bottom:16px">
        <el-col :span="8">
          <el-card shadow="never">
            <div class="stat-card">
              <div class="stat-label">合同总金额</div>
              <div class="stat-value" style="color:#409eff">¥ {{ fmt(stats?.total_contract ?? 0) }}</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card shadow="never">
            <div class="stat-card">
              <div class="stat-label">已收金额</div>
              <div class="stat-value" style="color:#67c23a">¥ {{ fmt(stats?.total_received ?? 0) }}</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card shadow="never">
            <div class="stat-card">
              <div class="stat-label">待收金额</div>
              <div class="stat-value" style="color:#e6a23c">¥ {{ fmt(stats?.total_unpaid ?? 0) }}</div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="16" style="margin-bottom:16px">
        <!-- 收款状态分布 -->
        <el-col :span="8">
          <el-card shadow="never" header="收款状态分布">
            <el-empty v-if="!stats || !Object.keys(stats.status_dist).length" description="暂无数据" :image-size="50" />
            <div v-else>
              <div
                v-for="(cnt, status) in stats.status_dist"
                :key="status"
                style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px"
              >
                <el-tag :type="statusTagType(String(status))" size="small">{{ status }}</el-tag>
                <span style="font-weight:600">{{ cnt }} 笔</span>
              </div>
            </div>
          </el-card>
        </el-col>

        <!-- 发票统计 -->
        <el-col :span="16">
          <el-card shadow="never" header="发票统计">
            <el-empty v-if="!stats?.invoice_stats?.length" description="暂无发票数据" :image-size="50" />
            <el-table v-else :data="stats.invoice_stats" size="small">
              <el-table-column label="状态" prop="status" width="100">
                <template #default="{ row }">
                  <el-tag :type="invoiceStatusType(row.status)" size="small">{{ row.status }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="笔数" prop="count" width="80" align="center" />
              <el-table-column label="金额" align="right">
                <template #default="{ row }">¥ {{ fmt(row.amount) }}</template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-col>
      </el-row>

      <!-- 月度收款趋势 -->
      <el-card shadow="never" :header="`${year} 年月度收款趋势`">
        <el-empty v-if="!stats" description="暂无数据" :image-size="50" />
        <div v-else style="padding:8px 0">
          <div
            v-for="(item, i) in stats.monthly_series"
            :key="item.month"
            style="display:flex;align-items:center;margin-bottom:10px;gap:8px"
          >
            <span style="width:32px;text-align:right;font-size:12px;color:#909399">{{ MONTHS[i] }}</span>
            <div style="flex:1;background:#f5f7fa;border-radius:3px;height:20px;overflow:hidden">
              <div
                :style="{
                  width: barWidth(item.received),
                  background: item.received > 0 ? '#67c23a' : 'transparent',
                  height: '100%',
                  transition: 'width 0.4s',
                  borderRadius: '3px',
                }"
              />
            </div>
            <span style="width:110px;text-align:right;font-size:12px;font-weight:600;color:#606266">
              {{ item.received > 0 ? '¥ ' + fmt(item.received) : '-' }}
            </span>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<style scoped>
.page-container { padding: 20px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { margin: 0; font-size: 20px; }
.stat-card { text-align: center; padding: 8px 0; }
.stat-label { font-size: 13px; color: #909399; margin-bottom: 6px; }
.stat-value { font-size: 22px; font-weight: bold; }
</style>
