/**
 * 客户证言轮播组件（简化版）
 * Testimonial carousel - showcase customer reviews
 */
import { Star, Quote } from "lucide-react";
import Image from "next/image";

// 演示数据 - 后续可替换为真实数据
const testimonials = [
  {
    id: "1",
    name: "张工",
    role: "独立开发者",
    company: "自由职业",
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Felix",
    content: "原本以为准备软著材料要花好几天，结果上传代码后30分钟就搞定了，格式完全符合要求，一次通过！太神奇了。",
    rating: 5,
    projectType: "copyright" as const,
  },
  {
    id: "2",
    name: "李明",
    role: "CTO",
    company: "某科技公司",
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Robert",
    content: "我们公司有20多个软件产品需要申请软著，用IPFlow批量处理，节省了大量人力成本。团队协作功能非常好用。",
    rating: 5,
    projectType: "copyright" as const,
  },
  {
    id: "3",
    name: "王芳",
    role: "知识产权专员",
    company: "某代理机构",
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Sarah",
    content: "作为知识产权代理机构，IPFlow大大提高了我们的工作效率。AI生成的说明书质量很高，只需微调就能使用。",
    rating: 5,
    projectType: "copyright" as const,
  },
  {
    id: "4",
    name: "赵强",
    role: "创业者",
    company: "初创公司",
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=John",
    content: "申请软著是我们创业路上的重要一步。IPFlow让这个过程变得异常简单，价格也很实惠，强烈推荐！",
    rating: 5,
    projectType: "copyright" as const,
  },
  {
    id: "5",
    name: "陈宇",
    role: "研发总监",
    company: "智能硬件企业",
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Michael",
    content: "发明专利的权利要求书一直是我们最头疼的环节，IPFlow辅助生成的初稿逻辑清晰、覆盖全面，配合工程师微调后很快定稿，申请周期明显缩短。",
    rating: 5,
    projectType: "patent" as const,
  },
  {
    id: "6",
    name: "林婷",
    role: "品牌经理",
    company: "新消费品牌",
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Emma",
    content: "一次要注册十几个类别的商标，尼斯分类查询和图样整理原本特别繁琐。IPFlow把材料清单梳理得明明白白，多件申请也能井井有条。",
    rating: 5,
    projectType: "trademark" as const,
  },
];

const projectTypeLabels = {
  copyright: "软著申请",
  patent: "专利申请",
  trademark: "商标注册",
};

export function TestimonialCarousel() {
  return (
    <section className="py-24 bg-muted/30">
      <div className="container">
        {/* Section Header */}
        <div className="text-center max-w-2xl mx-auto mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            用户真实评价
          </h2>
          <p className="text-lg text-muted-foreground">
            来自 5000+ 用户的真实反馈，看看他们如何评价 IPFlow
          </p>
        </div>

        {/* Testimonials Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {testimonials.map((testimonial) => (
            <div
              key={testimonial.id}
              className="bg-card border rounded-xl p-6 space-y-4"
            >
              {/* Quote Icon */}
              <Quote className="h-8 w-8 text-muted-foreground/20" />

              {/* Content */}
              <p className="text-muted-foreground leading-relaxed">
                {testimonial.content}
              </p>

              {/* Rating */}
              <div className="flex items-center gap-1">
                {[...Array(testimonial.rating)].map((_, i) => (
                  <Star
                    key={i}
                    className="h-4 w-4 fill-yellow-400 text-yellow-400"
                  />
                ))}
              </div>

              {/* Author */}
              <div className="flex items-center gap-3 pt-4 border-t">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10">
                  <span className="text-sm font-medium text-primary">
                    {testimonial.name.charAt(0)}
                  </span>
                </div>
                <div className="flex-1">
                  <div className="font-medium">{testimonial.name}</div>
                  <div className="text-sm text-muted-foreground">
                    {testimonial.role} · {testimonial.company}
                  </div>
                </div>
              </div>

              {/* Project Type Badge */}
              <div className="text-xs text-muted-foreground bg-muted inline-flex px-2 py-1 rounded">
                {projectTypeLabels[testimonial.projectType]}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
