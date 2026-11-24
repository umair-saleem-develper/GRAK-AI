"use client";
import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Modal } from "@/components/ui/modal";
import { Dialog } from "@/components/ui/dialog";
import { Dropdown, DropdownItem } from "@/components/ui/dropdown";
import { Tooltip } from "@/components/ui/tooltip";
import { Toast } from "@/components/ui/toast";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Avatar } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Spinner } from "@/components/ui/spinner";

export default function DesignSystem() {
  const [isModalOpen, setModalOpen] = useState(false);
  const [isDialogOpen, setDialogOpen] = useState(false);
  const [isDropdownOpen, setDropdownOpen] = useState(false);

  return (
    <div className="p-10 space-y-12 bg-background min-h-screen text-foreground pb-32">
      <h1 className="text-3xl font-bold text-primary">
        Grak AI - Atomic UI Design System
      </h1>

      <section>
        <h2 className="text-xl font-semibold mb-4 border-b border-white/10 pb-2">
          1. Buttons
        </h2>
        <div className="flex flex-wrap gap-4">
          <Button variant="default">Default Button</Button>
          <Button variant="primary">Primary Button</Button>
          <Button variant="outline">Outline Button</Button>
          <Button variant="ghost">Ghost Button</Button>
          <Button variant="glass">Glass Button</Button>
        </div>
      </section>

      <section>
        <h2 className="text-xl font-semibold mb-4 border-b border-white/10 pb-2">
          2. Inputs
        </h2>
        <div className="max-w-md">
          <Input placeholder="Enter your email address..." type="email" />
        </div>
      </section>

      <section>
        <h2 className="text-xl font-semibold mb-4 border-b border-white/10 pb-2">
          3. Badges & Avatars
        </h2>
        <div className="flex items-center gap-6">
          <Badge variant="default">Default Badge</Badge>
          <Badge variant="secondary">Secondary Badge</Badge>
          <Badge variant="destructive">Destructive Badge</Badge>
          <Badge variant="outline">Outline Badge</Badge>
          <div className="w-px h-8 bg-white/10"></div>
          <Avatar fallback="GK" size="sm" />
          <Avatar fallback="GK" size="md" />
          <Avatar fallback="GK" size="lg" />
        </div>
      </section>

      <section>
        <h2 className="text-xl font-semibold mb-4 border-b border-white/10 pb-2">
          4. Cards & Skeletons
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl">
          <Card className="glass-card">
            <CardHeader>
              <CardTitle>Premium Glass Card</CardTitle>
            </CardHeader>
            <CardContent>
              This is a standard card component leveraging the generic Card
              layout but utilizing the utility .glass-card class from
              globals.css for a premium feel.
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Loading State (Skeleton)</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <Skeleton className="h-4 w-[250px]" />
              <Skeleton className="h-4 w-[200px]" />
              <div className="flex items-center gap-2 mt-4">
                <Spinner size={16} />{" "}
                <span className="text-sm text-muted-foreground">
                  Generating response...
                </span>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>

      <section>
        <h2 className="text-xl font-semibold mb-4 border-b border-white/10 pb-2">
          5. Interactive Elements (Tooltips, Dropdowns)
        </h2>
        <div className="flex items-center gap-8">
          <Tooltip content="This is a very helpful tooltip!" side="top">
            <Badge variant="secondary" className="cursor-help py-1 px-3">
              Hover me for Tooltip
            </Badge>
          </Tooltip>

          <Dropdown
            isOpen={isDropdownOpen}
            onClose={() => setDropdownOpen(false)}
            trigger={
              <Button variant="outline" onClick={() => setDropdownOpen(true)}>
                Open Dropdown
              </Button>
            }
          >
            <DropdownItem>Account Settings</DropdownItem>
            <DropdownItem>Billing</DropdownItem>
            <DropdownItem destructive>Logout</DropdownItem>
          </Dropdown>
        </div>
      </section>

      <section>
        <h2 className="text-xl font-semibold mb-4 border-b border-white/10 pb-2">
          6. Modals, Dialogs, & Toasts
        </h2>
        <div className="flex items-center gap-4">
          <Button variant="primary" onClick={() => setModalOpen(true)}>
            Open Basic Modal
          </Button>
          <Modal isOpen={isModalOpen} onClose={() => setModalOpen(false)}>
            <div className="p-4">
              <h3 className="text-lg font-bold mb-2">Basic Modal Content</h3>
              <p className="text-gray-400">
                This is a highly reusable, animated modal component.
              </p>
              <Button
                className="mt-4 w-full"
                onClick={() => setModalOpen(false)}
              >
                Close Modal
              </Button>
            </div>
          </Modal>

          <Button variant="outline" onClick={() => setDialogOpen(true)}>
            Open Action Dialog
          </Button>
          <Dialog
            isOpen={isDialogOpen}
            onClose={() => setDialogOpen(false)}
            title="Are you absolutely sure?"
            description="This action cannot be undone. This will permanently delete your conversation."
            actionText="Delete Conversation"
            onAction={() => setDialogOpen(false)}
          >
            <div className="text-sm text-gray-400">
              Additional content can be passed as children here.
            </div>
          </Dialog>
        </div>

        <div className="mt-6">
          <p className="text-sm text-gray-400 mb-3">
            Example Toast (rendered inline for demonstration):
          </p>
          <div className="max-w-sm">
            <Toast
              title="Configuration saved"
              description="Your settings have been successfully updated."
              onClose={() => {}}
            />
          </div>
        </div>
      </section>
    </div>
  );
}
