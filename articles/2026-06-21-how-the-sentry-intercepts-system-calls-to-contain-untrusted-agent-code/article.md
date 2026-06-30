---
title: "How the Sentry Intercepts System Calls to Contain Untrusted Agent Code"
author: "Dr. Hernani Costa"
author_url: "https://drhernanicosta.com"
author_linkedin: "https://www.linkedin.com/in/hernani-costa-ai-ceo-firstaimovers/"
publication: "First AI Movers"
publication_url: "https://firstaimovers.com"
canonical_url: "https://radar.firstaimovers.com/how-the-sentry-intercepts-system-calls-to-contain-untrusted-agent-code"
published_date: "2026-06-21"
license: "CC BY 4.0"
---

> **TL;DR:** The Sentry in gVisor mediates every system call from untrusted code, reducing the host attack surface. Learn how interception works and why it matters for

When you run model-generated code or third-party agents, you need more than a container-you need a boundary that redefines what "system call" means. In a gVisor sandbox, that boundary is the Sentry, an application kernel that sits between your code and the host kernel, intercepting every system call and implementing a restricted System API. This is not just a layer; it is a deliberate down-scope of host interaction. The Sentry's own access to the host system API is minimized, so even a successful exploit within the sandbox is contained against the Sentry, not the host. Understanding this interception model turns "use a sandbox" into a concrete, measurable claim about which host interactions untrusted code can actually reach. For engineering teams at small to medium companies, that means you can confidently deploy AI-generated agents or process arbitrary user uploads, knowing that the Sentry's mediation shrinks the host attack surface to a safer, smaller set of operations.

## The Sentry as an Application Kernel

In a standard container, the application talks directly to the host kernel; every system call goes from the containerized process to the host's syscall interface. gVisor changes this by inserting the Sentry. The Sentry is a user-space process that implements the Linux kernel API, handling system calls from the sandboxed application. The platform beneath (such as KVM or ptrace) ensures that all application system calls are trapped and sent to the Sentry. The Sentry then decides how to handle each call: many are serviced entirely within the Sentry's own logic, while a subset must be forwarded to the host kernel after the Sentry applies its own policies and transformations.

This architecture means the application's view of the kernel is entirely mediated. The Sentry does not simply pass through syscalls; it actively implements them. For example, a file read request does not result in a direct read() syscall to the host. Instead, the Sentry maintains its own file descriptor table, processes the request, and if the file resides on a host filesystem, it communicates with a separate file proxy called the Gofer via the LISAFS protocol. This decoupling ensures that the host kernel is exposed only to a carefully controlled set of operations from the Sentry, not the raw, unfiltered requests of untrusted code.

## How System Call Interception Contains Exploits

The containment promise of gVisor depends on this indirection. An attacker who compromises an application inside a plain container can invoke any host kernel system call permitted by the container's seccomp profile. While seccomp restricts the set, the vulnerability surface remains the kernel itself. In gVisor, the attacker never directly reaches the host kernel; they only interact with the Sentry. Even if the attacker finds a way to exploit a flaw in the Sentry's emulation of a system call, they gain control over the Sentry process, not the host kernel. The Sentry runs with limited privileges and uses a narrow, curated set of host system calls for its own needs-typically far fewer than what a containerized application would require.

This defense in depth is analogous to an air gap at the system-call layer. The Sentry's task is to be a gatekeeper that validates and sanitizes every interaction before it ever reaches the host. Because the Sentry itself is not the kernel, a compromise is measurable: the attacker might corrupt the Sentry's memory, but they cannot directly escalate to host kernel code execution unless they can break out of the user-space Sentry process. That requires another vulnerability, adding a costly step to the attack chain.

## The Role of the Gofer Filesystem Proxy

Filesystem access is a primary vector for host compromise. gVisor isolates this further by separating the Sentry from direct filesystem access. Instead, the Sentry communicates with a Gofer process that acts as a file proxy. Gofer instances run outside the sandbox, isolated from the application, and they talk to the Sentry using the LISAFS protocol. When the Sentry needs to read or write a file on behalf of the sandboxed application, it sends a request to the Gofer, which performs the actual host filesystem operations. This means the Sentry itself never needs to open host files directly-another layer of defense.

To prevent the sandbox from modifying the host filesystem, administrators can configure a writable overlay on top of read-only mounts. All modifications are written to the overlay, leaving the underlying host filesystem untouched. This is especially powerful for build pipelines or AI agent runs where you want the sandbox to believe it has a writable root but you never want those changes to persist to the host. Global configuration with the --overlay2 flag (e.g., --overlay2=root:memory,size=2g) allows setting this for every container without per-container repetition.

## Practical Configuration for Defense in Depth

The Sentry's isolation is reinforced by how gVisor interacts with host resource controls. By default, runsc creates and manages cgroups using the fs cgroup driver. However, when run with --systemd-cgroup, it delegates cgroup management to systemd over dbus, creating transient units for each container. This requires host systemd version 244 or newer and unified cgroups (cgroupv2). In this mode, runsc sets accounting for all controllers: CPUAccounting, IOAccounting, MemoryAccounting, and TasksAccounting, regardless of whether limits are specified. Resource limits are translated from the runtime spec to systemd unit properties. The container's unit is placed into a slice derived from the specification; if a CgroupsPath is set in the form [slice]:[prefix]:[name], that slice is used. If the slice contains dashes, they denote sub-slices (e.g., user-1000.slice is a subslice of user.slice). This integration ensures that the host's cgroup enforcement remains abstracted away from direct application interference, reinforcing the boundary.

For teams that need to checkpoint and restore sandbox state, gVisor supports filesystem snapshots. The runsc fscheckpoint command saves all root filesystem changes in a sandbox (across all containers) to a directory specified with --image-path. These snapshots are more efficient than rootfs tar snapshots: they allow containers to begin executing while restore is in progress, store sparse files more effectively, and achieve higher throughput subject to disk limits. To restore, you pass --fs-restore-image-path to runsc create or run. However, the root filesystem must be an overlay with a disk-backed tmpfs upper layer; non-root tmpfs overlays created by --overlay2 with mount specifier "all" are not included. This feature underscores that defense in depth extends to operational tooling: even when saving and loading state, the isolation assumptions hold.

## Frequently Asked Questions

### Q: Does the Sentry prevent all host kernel exploits?

No, but it dramatically reduces the attack surface. The Sentry limits which host system calls are ever issued. If a host kernel vulnerability exists in a syscall that the Sentry does not use, it is effectively unreachable from the sandbox. This is a meaningful reduction compared to direct-kernel containers.

### Q: How does the Sentry intercept system calls?

It relies on a platform such as KVM to trap the application's syscall instructions. When the application issues a syscall, the platform halts the virtual CPU and delivers the event to the Sentry. The Sentry then dispatches the request to its own handler. The application cannot bypass this mechanism because the platform enforces the trap at the hardware level.

### Q: What about performance overhead?

There is overhead because system calls are emulated in user space. However, gVisor includes optimizations like Directfs for some filesystem operations, and the performance impact varies by workload. The trade-off is acceptable for many use cases where security isolation is non-negotiable. Administrators can further tune by choosing overlay backing mediums that align with memory and disk performance profiles.

### Q: How is gVisor different from a container with a strict seccomp profile?

Seccomp filters still route system calls to the host kernel; they only allow or deny specific syscall numbers. gVisor completely replaces the kernel interface with the Sentry's implementation. This means even permitted syscalls are not processed by the host kernel in the same way; they are interpreted by the Sentry, which can add additional validation and context that seccomp cannot provide.

## Further Reading

- [Canonical Docs Are the Most Underrated AI Memory System](https://radar.firstaimovers.com/canonical-docs-ai-memory-system-2026)
- [Skills, Memory, and Agent Harnesses Are the Next AI Platform Layer](https://radar.firstaimovers.com/skills-memory-agent-harnesses-next-ai-layer-2026)
- [How to Run a 30-Day Pilot for an Open-Source AI Coding Agent](https://radar.firstaimovers.com/30-day-pilot-open-source-ai-coding-agent-2026)
- [The Memory Layer Enterprises Actually Need for AI Agents](https://radar.firstaimovers.com/enterprise-ai-agent-memory-layer-2026)
- [Why Agentic AI Pilots Die at Production: The Implementation Layer No Vendor Replaces](https://radar.firstaimovers.com/why-agentic-ai-pilots-die-at-production-2026)

<!-- structured-data
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "How the Sentry Intercepts System Calls to Contain Untrusted Agent Code",
  "description": "The Sentry in gVisor mediates every system call from untrusted code, reducing the host attack surface. Learn how interception works and why it matters for",
  "datePublished": "2026-06-21T06:48:51.933996+00:00",
  "dateModified": "2026-06-21T06:48:51.933996+00:00",
  "author": {
    "@type": "Person",
    "@id": "https://radar.firstaimovers.com/page/dr-hernani-costa#dr-hernani-costa",
    "name": "Dr. Hernani Costa",
    "url": "https://radar.firstaimovers.com/page/dr-hernani-costa"
  },
  "publisher": {
    "@type": "Organization",
    "name": "First AI Movers",
    "url": "https://radar.firstaimovers.com",
    "logo": {
      "@type": "ImageObject",
      "url": "https://radar.firstaimovers.com/favicon.ico"
    }
  },
  "mainEntityOfPage": {
    "@type": "WebPage",
    "@id": "https://radar.firstaimovers.com/how-the-sentry-intercepts-system-calls-to-contain-untrusted-agent-code"
  },
  "image": "https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=1200&h=630&fit=crop&q=80",
  "speakable": {
    "@type": "SpeakableSpecification",
    "cssSelector": [
      ".article-body > p:first-of-type",
      ".article-body > p:nth-of-type(2)"
    ],
    "xpath": [
      "/html/body//article//p[1]",
      "/html/body//article//p[2]"
    ]
  }
}
</script>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Q: Does the Sentry prevent all host kernel exploits?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "No, but it dramatically reduces the attack surface. The Sentry limits which host system calls are ever issued. If a host kernel vulnerability exists in a syscall that the Sentry does not use, it is effectively unreachable from the sandbox. This is a meaningful reduction compared to direct-kernel ..."
      }
    },
    {
      "@type": "Question",
      "name": "Q: How does the Sentry intercept system calls?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "It relies on a platform such as KVM to trap the application's syscall instructions. When the application issues a syscall, the platform halts the virtual CPU and delivers the event to the Sentry. The Sentry then dispatches the request to its own handler. The application cannot bypass this mechani..."
      }
    },
    {
      "@type": "Question",
      "name": "Q: What about performance overhead?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "There is overhead because system calls are emulated in user space. However, gVisor includes optimizations like Directfs for some filesystem operations, and the performance impact varies by workload. The trade-off is acceptable for many use cases where security isolation is non-negotiable. Adminis..."
      }
    },
    {
      "@type": "Question",
      "name": "Q: How is gVisor different from a container with a strict seccomp profile?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Seccomp filters still route system calls to the host kernel; they only allow or deny specific syscall numbers. gVisor completely replaces the kernel interface with the Sentry's implementation. This means even permitted syscalls are not processed by the host kernel in the same way; they are interp..."
      }
    }
  ]
}
</script>
-->