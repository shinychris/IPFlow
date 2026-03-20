/**
 * FAQ 折叠面板组件
 * FAQ section - frequently asked questions
 */
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

const faqs = [
  {
    category: "基础问题",
    questions: [
      {
        q: "什么是 IPFlow？",
        a: "IPFlow 是一个专业的知识产权申请管理平台，利用 AI 技术帮助用户快速生成软著、专利、商标申请材料。我们致力于让知识产权申请变得简单、高效、可靠。",
      },
      {
        q: "现在有免费版吗？",
        a: "目前已取消免费版，新增按次付费方案：¥19.0/次。适合低频、轻量的单次申请需求。",
      },
      {
        q: "生成的材料符合版权中心要求吗？",
        a: "是的！我们内置了中国版权中心最新的格式规范，所有生成的材料都严格按照要求排版。我们的首审通过率达到89%，远高于行业平均水平。",
      },
    ],
  },
  {
    category: "定价与支付",
    questions: [
      {
        q: "支持哪些支付方式？",
        a: "我们支持微信支付、支付宝以及银行卡支付。对于企业客户，我们也支持对公转账和发票开具。",
      },
      {
        q: "如果申请未通过可以退款吗？",
        a: "可以。对于未通过场景，您可联系在线客服申请退款，我们会根据订单与审核结果协助处理。",
      },
      {
        q: "年付有什么优惠？",
        a: "年付可以享受约17%的折扣。例如基础版年付仅需¥490，比月付（¥588）节省¥98。",
      },
      {
        q: "可以随时取消订阅吗？",
        a: "可以。您可以随时在设置中取消订阅，取消后将在当前计费周期结束后停止续费。已生成的内容不会受影响。",
      },
      {
        q: "如何升级或降级套餐？",
        a: "您可以在控制台的订阅管理页面随时升级或降级套餐。升级立即生效，降级在当前计费周期结束后生效。",
      },
    ],
  },
  {
    category: "使用问题",
    questions: [
      {
        q: "支持哪些编程语言的代码处理？",
        a: "我们支持40+主流编程语言，包括但不限于：Python、JavaScript、TypeScript、Java、C/C++、C#、Go、Rust、PHP、Ruby、Swift、Kotlin等。",
      },
      {
        q: "生成一个软著申请材料需要多长时间？",
        a: "平均约30分钟。具体时间取决于代码量和复杂度。上传代码（2分钟）→填写信息（3分钟）→AI生成（20分钟）→导出提交（1分钟）。",
      },
      {
        q: "生成的材料可以修改吗？",
        a: "当然可以。我们提供完整的在线编辑器，您可以随时修改生成的任何内容，包括说明书、代码排版等。",
      },
      {
        q: "团队协作功能如何使用？",
        a: "专业版及以上支持团队协作。您可以邀请团队成员加入组织，分配不同权限（管理员、成员、查看者），协同完成申请材料准备。",
      },
    ],
  },
  {
    category: "安全与隐私",
    questions: [
      {
        q: "我的代码安全吗？",
        a: "绝对安全。我们采用企业级加密技术保护您的数据，所有传输均使用SSL/TLS加密。我们不会将您的代码用于任何其他目的，也不会与第三方共享。",
      },
      {
        q: "数据存储在哪里？",
        a: "我们的服务器位于中国境内的符合安全标准的数据中心，符合《网络安全法》和《数据安全法》的要求。",
      },
      {
        q: "可以删除我的数据吗？",
        a: "可以。您可以随时删除项目和上传的文件。删除后数据将从我们的服务器中永久移除，无法恢复。",
      },
    ],
  },
];

export function FAQSection() {
  return (
    <section className="py-24">
      <div className="container">
        <div className="text-center max-w-2xl mx-auto mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            常见问题
          </h2>
          <p className="text-lg text-muted-foreground">
            查找关于定价、使用和安全的常见问题解答
          </p>
        </div>

        <div className="max-w-3xl mx-auto space-y-12">
          {faqs.map((section) => (
            <div key={section.category}>
              <h3 className="text-xl font-bold mb-6">{section.category}</h3>
              <Accordion type="multiple" className="space-y-4">
                {section.questions.map((faq, index) => (
                  <AccordionItem
                    key={index}
                    value={`item-${index}`}
                    className="border rounded-lg px-6"
                  >
                    <AccordionTrigger className="text-left hover:no-underline">
                      {faq.q}
                    </AccordionTrigger>
                    <AccordionContent className="text-muted-foreground pt-2">
                      {faq.a}
                    </AccordionContent>
                  </AccordionItem>
                ))}
              </Accordion>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
