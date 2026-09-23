"use client";

import { useState } from "react";
import { Button } from "@/components/atoms/Button";
import { Heading } from "@/components/atoms/Heading";
import { ChangePasswordForm } from "@/components/molecules/ChangePasswordForm";
import { Modal } from "@/components/molecules/Modal";
import { ProfileForm } from "@/components/molecules/ProfileForm";
import { PageTemplate } from "@/components/templates/PageTemplate";
import { useProfile } from "@/hooks/useProfile";

export default function AccountPage() {
  const { profile, isLoading, error, save } = useProfile();
  const [isPasswordModalOpen, setIsPasswordModalOpen] = useState(false);

  return (
    <PageTemplate title="Account">
      {isLoading ? (
        <p className="text-sm text-muted">Loading...</p>
      ) : !profile ? (
        <p role="alert" className="text-sm text-danger">
          {error ?? "Could not load your profile."}
        </p>
      ) : (
        <div className="flex max-w-md flex-col gap-8">
          <div className="flex flex-col gap-4">
            <Heading as="h2">Profile</Heading>
            <ProfileForm profile={profile} onSave={save} />
          </div>
          <div className="flex flex-col gap-4 border-t border-border pt-6">
            <Heading as="h2">Password</Heading>
            <Button
              type="button"
              variant="ghost"
              onClick={() => setIsPasswordModalOpen(true)}
              className="w-fit"
            >
              Change password
            </Button>
          </div>
        </div>
      )}
      <Modal
        isOpen={isPasswordModalOpen}
        onClose={() => setIsPasswordModalOpen(false)}
        title="Change password"
      >
        <ChangePasswordForm onSuccess={() => setIsPasswordModalOpen(false)} />
      </Modal>
    </PageTemplate>
  );
}
