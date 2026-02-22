<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { contractApi, type ContractDetail, type PaymentRecord } from '@/api/contract'
import AttachmentPanel from '@/components/common/AttachmentPanel.vue'

const route = useRoute()
const router = useRouter()
const contractId = route.params.id as string

const contract = ref<ContractDetail | null>(null)
const paymentRecords = ref<PaymentRecord[]>([])
const loading = ref(false)

// 收款表单
const recForm = ref({
  plan_id: '',
  received_amount: 0,
  received_date: '',
  payment_method: '对公转账',
  bank_reference: '',
  remark: '',
})
const recSaving = ref(false)
const paymentMethodOptions = ['对公转账', '现金', '支票', '其他']

async function load() {
  loading.value = true
  try {
    const [cRes, rRes] = await Promise.all([
      contractApi.get(contractId),
      contractApi.listPaymentRecords(contractId),
    ])
    contract.value = cRes.data
    paymentRecords.value = rRes.data
  } finally {
    loading.value = false
  }
}

async function addRecord() {
  if (!recForm.value.plan_id) { ElMessage.warning('请选择付款期次'); return }
  if (!recForm.value.received_date) { ElMessage.warning('请选择收款日期'); return }
  if (!recForm.value.received_amount) { ElMessage.warning('请填写收款金额'); return }
  recSaving.value = true
  try {
    await contractApi.addPaymentRecord(contractId, { ...recForm.value })
    ElMessage.success('收款已记录')
    recForm.value = { plan_id: '', received_amount: 0, received_date: '', payment_method: '对公转账', bank_reference: '', remark: '' }
    await load()
  } finally {
    recSaving.value = false
  }
}

const statusTagType = (s: string) =>
  ({ '草稿': 'info', '审批中': 'warning', '待签署': 'warning', '执行中': 'primary',
     '已完成': 'success', '已终止': 'danger' }[s] ?? '') as any

const planStatusType = (s: string) =>
  ({ '待支付': 'info', '部分支付': 'warning', '已支付': 'success', '已逾期': 'danger' }[s] ?? '') as any

// Paid amount per plan

const totalReceived = () => paymentRecords.value.reduce((s, r) => s + Number(r.received_amount), 0)

onMounted(load)
</script>

<template>
  <div v-loading="loading">
    <el-page-header @back="router.back()" style="margin-bottom:16px">
      <template #content>
        <span>{{ contract?.contract_no }} - {{ contract?.contract_name }}</span>
      </template>
    </el-page-header>

    <el-row :gutter="16">
      <!-- 左侧：合同信息 + 服务明细 -->
      <el-col :span="16">
        <el-card shadow="never" style="margin-bottom:16px">
          <template #header><span>合同基本信息</span></template>
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item label="合同编号">{{ contract?.contract_no }}</el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="statusTagType(contract?.status ?? '')" size="small">{{ contract?.status }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="合同名称" :span="2">{{ contract?.contract_name }}</el-descriptions-item>
            <el-descriptions-item label="认证标准">{{ contract?.certification_standard }}</el-descriptions-item>
            <el-descriptions-item label="合同类型">{{ contract?.contract_type }}</el-descriptions-item>
            <el-descriptions-item label="合同金额">
              <span style="font-weight:600;color:#409eff">{{ Number(contract?.total_amount ?? 0).toLocaleString() }} 元</span>
            </el-descriptions-item>
            <el-descriptions-item label="税率">{{ contract?.tax_rate ?? '-' }}%</el-descriptions-item>
            <el-descriptions-item label="签署日期">{{ contract?.sign_date ?? '-' }}</el-descriptions-item>
            <el-descriptions-item label="开始日期">{{ contract?.start_date ?? '-' }}</el-descriptions-item>
            <el-descriptions-item label="到期日期">{{ contract?.end_date ?? '-' }}</el-descriptions-item>
            <el-descriptions-item label="已收款">
              <span style="font-weight:600;color:#67c23a">{{ totalReceived().toLocaleString() }} 元</span>
            </el-descriptions-item>
            <el-descriptions-item label="服务范围" :span="2">{{ contract?.service_scope }}</el-descriptions-item>
            <el-descriptions-item label="备注" :span="2">{{ contract?.remark ?? '-' }}</el-descriptions-item>
          </el-descriptions>
        </el-card>

        <el-card shadow="never">
          <template #header><span>服务明细</span></template>
          <el-table :data="contract?.items ?? []" size="small" border>
            <el-table-column prop="item_name" label="服务名称" min-width="140" />
            <el-table-column prop="standard" label="标准" width="110" />
            <el-table-column prop="item_type" label="类型" width="90" />
            <el-table-column prop="audit_days" label="人天" width="70" align="center" />
            <el-table-column prop="unit_price" label="单价" width="100" align="right">
              <template #default="{ row }">{{ Number(row.unit_price).toLocaleString() }}</template>
            </el-table-column>
            <el-table-column prop="quantity" label="数量" width="70" align="center" />
            <el-table-column prop="discount" label="折扣" width="70" align="center" />
            <el-table-column prop="amount" label="金额" width="110" align="right">
              <template #default="{ row }">
                <span style="font-weight:600">{{ Number(row.amount).toLocaleString() }}</span>
              </template>
            </el-table-column>
          </el-table>
        </el-card>

        <el-card shadow="never" style="margin-top:16px">
          <AttachmentPanel entity-type="contract" :entity-id="contractId" />
        </el-card>
      </el-col>

      <!-- 右侧：付款计划 + 收款记录 -->
      <el-col :span="8">
        <el-card shadow="never" style="margin-bottom:16px">
          <template #header><span>付款计划</span></template>
          <el-table :data="contract?.payment_plans ?? []" size="small">
            <el-table-column prop="installment_no" label="期" width="40" align="center" />
            <el-table-column prop="description" label="说明" />
            <el-table-column prop="plan_amount" label="计划金额" width="90" align="right">
              <template #default="{ row }">{{ Number(row.plan_amount).toLocaleString() }}</template>
            </el-table-column>
            <el-table-column prop="due_date" label="应付日" width="100" />
            <el-table-column label="状态" width="80" align="center">
              <template #default="{ row }">
                <el-tag :type="planStatusType(row.status)" size="small">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>

        <el-card shadow="never">
          <template #header><span>收款记录</span></template>

          <!-- 新增收款 -->
          <div style="margin-bottom:12px;padding-bottom:12px;border-bottom:1px solid #f0f0f0">
            <div style="font-size:12px;font-weight:600;margin-bottom:8px;color:#606266">登记收款</div>
            <el-select v-model="recForm.plan_id" placeholder="选择付款期" size="small" style="width:100%;margin-bottom:6px">
              <el-option
                v-for="p in contract?.payment_plans ?? []"
                :key="p.id"
                :label="`第${p.installment_no}期 ${p.description ?? ''} (${Number(p.plan_amount).toLocaleString()})`"
                :value="p.id"
              />
            </el-select>
            <el-row :gutter="6">
              <el-col :span="12">
                <el-input-number v-model="recForm.received_amount" :min="0" :precision="2" size="small"
                  placeholder="收款金额" style="width:100%" />
              </el-col>
              <el-col :span="12">
                <el-date-picker v-model="recForm.received_date" type="date" value-format="YYYY-MM-DD"
                  placeholder="收款日期" size="small" style="width:100%" />
              </el-col>
            </el-row>
            <el-select v-model="recForm.payment_method" size="small" style="width:100%;margin-top:6px">
              <el-option v-for="m in paymentMethodOptions" :key="m" :label="m" :value="m" />
            </el-select>
            <el-input v-model="recForm.bank_reference" placeholder="银行流水号（选填）" size="small"
              style="margin-top:6px" />
            <el-button type="primary" size="small" :loading="recSaving"
              style="margin-top:6px;width:100%" @click="addRecord">登记收款</el-button>
          </div>

          <!-- 历史收款 -->
          <el-timeline>
            <el-timeline-item
              v-for="r in paymentRecords"
              :key="r.id"
              :timestamp="r.received_date"
              placement="top"
            >
              <div style="font-size:12px">
                <el-tag size="small" style="margin-right:4px">{{ r.payment_method }}</el-tag>
                <span style="font-weight:600;color:#67c23a">{{ Number(r.received_amount).toLocaleString() }} 元</span>
                <div v-if="r.bank_reference" style="color:#909399;margin-top:2px">
                  流水号：{{ r.bank_reference }}
                </div>
                <div v-if="r.remark" style="color:#909399;margin-top:2px">{{ r.remark }}</div>
              </div>
            </el-timeline-item>
            <div v-if="paymentRecords.length === 0"
              style="color:#c0c4cc;text-align:center;padding:20px 0;font-size:13px">
              暂无收款记录
            </div>
          </el-timeline>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>
