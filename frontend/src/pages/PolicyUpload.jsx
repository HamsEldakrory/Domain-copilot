import { useState } from "react";

import {
  Container,
  Card,
  Form,
  Button,
  Row,
  Col,
  Alert,
} from "react-bootstrap";

import { useForm } from "react-hook-form";

import { useUploadPolicy } from "../hooks/usePolicies";

import { useDocumentStatus } from "../hooks/useDocuments";

export default function PolicyUpload() {
  const { register, handleSubmit } = useForm();

  const upload = useUploadPolicy();

  const [documentId, setDocumentId] = useState(null);

  const { data: documentStatus } = useDocumentStatus(
    documentId,
    Boolean(documentId),
  );

  const onSubmit = (data) => {
    const formData = new FormData();

    Object.entries(data).forEach(([key, value]) => {
      if (!value) {
        return;
      }

      if (key === "file") {
        formData.append(key, value[0]);
      } else {
        formData.append(key, value);
      }
    });

    upload.mutate(formData, {
      onSuccess: (response) => {
        setDocumentId(response.id);
      },
    });
  };

  return (
    <Container
      className="mt-4"
      style={{
        maxWidth: 600,
      }}
    >
      <Card body>
        <h5>Upload New Policy (Manager only)</h5>

        <Form onSubmit={handleSubmit(onSubmit)}>
          <Form.Group className="mb-2">
            <Form.Label>File (.pdf/.docx)</Form.Label>

            <Form.Control
              type="file"
              {...register("file", {
                required: true,
              })}
            />
          </Form.Group>

          <Row>
            <Col>
              <Form.Group className="mb-2">
                <Form.Label>Policy Number</Form.Label>

                <Form.Control
                  {...register("policy_number", {
                    required: true,
                  })}
                />
              </Form.Group>
            </Col>

            <Col>
              <Form.Group className="mb-2">
                <Form.Label>Version</Form.Label>

                <Form.Control
                  {...register("version", {
                    required: true,
                  })}
                />
              </Form.Group>
            </Col>
          </Row>

          <Row>
            <Col>
              <Form.Group className="mb-2">
                <Form.Label>Effective From</Form.Label>

                <Form.Control
                  type="date"
                  {...register("effective_from", {
                    required: true,
                  })}
                />
              </Form.Group>
            </Col>

            <Col>
              <Form.Group className="mb-2">
                <Form.Label>Effective To</Form.Label>

                <Form.Control type="date" {...register("effective_to")} />
              </Form.Group>
            </Col>
          </Row>

          <Row>
            <Col>
              <Form.Group className="mb-3">
                <Form.Label>Policy Limit</Form.Label>

                <Form.Control
                  type="number"
                  step="0.01"
                  {...register("policy_limit", {
                    required: true,
                  })}
                />
              </Form.Group>
            </Col>

            <Col>
              <Form.Group className="mb-3">
                <Form.Label>Deductible</Form.Label>

                <Form.Control
                  type="number"
                  step="0.01"
                  {...register("deductible", {
                    required: true,
                  })}
                />
              </Form.Group>
            </Col>
          </Row>

          <Button type="submit" disabled={upload.isPending}>
            {upload.isPending ? "Uploading..." : "Upload"}
          </Button>
        </Form>

        {documentId && documentStatus && (
          <Alert
            className="mt-3"
            variant={
              documentStatus.status === "ingested"
                ? "success"
                : documentStatus.status === "failed"
                  ? "danger"
                  : "info"
            }
          >
            Status: {documentStatus.status}
            {documentStatus.error_message &&
              ` — ${documentStatus.error_message}`}
          </Alert>
        )}
      </Card>
    </Container>
  );
}
