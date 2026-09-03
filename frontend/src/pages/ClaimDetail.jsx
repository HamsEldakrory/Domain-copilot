import { useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import {
  Container,
  Card,
  Form,
  Button,
  ListGroup,
  Table,
  Row,
  Col,
  Badge,
} from "react-bootstrap";
import { useForm } from "react-hook-form";
import { useSelector } from "react-redux";
import { useClaim } from "../hooks/useClaims";
import {
  useAsk,
  useAdjudicate,
  useApprovalDecision,
  useTrace,
} from "../hooks/useAdjudication";

export default function ClaimDetail() {
  const { claimId } = useParams();
  const { data: claim } = useClaim(claimId);
  const askForm = useForm();
  const runForm = useForm();
  const ask = useAsk();
  const adjudicate = useAdjudicate();
  const [askResult, setAskResult] = useState(null);
  const [jobId, setJobId] = useState(null);
  const [events, setEvents] = useState([]);
  const esRef = useRef(null);
  const access = useSelector((state) => state.auth.access);
  const approval = useApprovalDecision(jobId);
  const { data: trace, refetch: refetchTrace } = useTrace(jobId, false);
  useEffect(() => {
    return () => {
      esRef.current?.close();
    };
  }, []);

  const onAsk = (data) => {
    ask.mutate(data.query, {
      onSuccess: setAskResult,
    });
  };

  const onRun = (data) => {
    adjudicate.mutate(
      {
        claimId,
        claimedAmount: data.claimedAmount,
        deductibleOverride: data.deductibleOverride,
      },
      {
        onSuccess: (response) => {
          setJobId(response.job_id);
          setEvents([]);
          const eventSource = new EventSource(
            `${import.meta.env.VITE_API_BASE_URL}/jobs/${response.job_id}/stream/?access=${access}`,
          );
          const eventTypes = [
            "status",
            "agent_started",
            "agent_progress",
            "token",
            "agent_complete",
            "done",
          ];

          eventTypes.forEach((type) => {
            eventSource.addEventListener(type, (event) => {
              setEvents((previous) => [
                ...previous,
                {
                  type,
                  data: JSON.parse(event.data),
                },
              ]);
            });
          });

          esRef.current = eventSource;
        },
      },
    );
  };
  if (!claim) {
    return <Container className="mt-4">Loading...</Container>;
  }
  return (
    <Container className="mt-4">
      <h4>
        Claim {claim.claim_date}
        <Badge bg="secondary" className="ms-2">
          {claim.status}
        </Badge>
      </h4>
      {/* ASK */}
      <Card className="my-3" body>
        <h6>Ask a Question</h6>
        <Form onSubmit={askForm.handleSubmit(onAsk)}>
          <Row>
            <Col xs={9}>
              <Form.Control
                {...askForm.register("query", {
                  required: true,
                })}
                placeholder="e.g. What is the deductible?"
              />
            </Col>

            <Col xs={3}>
              <Button type="submit" className="w-100">
                Ask
              </Button>
            </Col>
          </Row>
        </Form>

        {askResult &&
          (askResult.refused ? (
            <p className="mt-2 text-muted">
              <i>{askResult.reason}</i>
            </p>
          ) : (
            <ListGroup className="mt-2">
              {askResult.citations?.map((citation, index) => (
                <ListGroup.Item key={index}>
                  <b>{citation.document}</b> — {citation.section}:{" "}
                  {citation.excerpt}
                </ListGroup.Item>
              ))}
            </ListGroup>
          ))}
      </Card>

      {/* ADJUDICATION */}

      <Card className="my-3" body>
        <h6>Run Adjudication</h6>

        <Form onSubmit={runForm.handleSubmit(onRun)}>
          <Row>
            <Col xs={4}>
              <Form.Label>Claimed Amount</Form.Label>

              <Form.Control
                type="number"
                step="0.01"
                {...runForm.register("claimedAmount", {
                  required: true,
                  min: 0,
                })}
              />
            </Col>

            <Col xs={4}>
              <Form.Label>Deductible Override (optional)</Form.Label>

              <Form.Control
                type="number"
                step="0.01"
                {...runForm.register("deductibleOverride")}
                placeholder="Uses policy default if blank"
              />
            </Col>

            <Col xs={4} className="d-flex align-items-end">
              <Button
                type="submit"
                className="w-100"
                disabled={adjudicate.isPending}
              >
                {adjudicate.isPending ? "Submitting..." : "Submit"}
              </Button>
            </Col>
          </Row>
        </Form>

        {jobId && <p className="mt-2 text-muted">Job: {jobId}</p>}

        <div
          style={{
            background: "#f8f9fa",
            padding: 8,
            maxHeight: 220,
            overflowY: "auto",
            fontSize: "0.85rem",
          }}
        >
          {events.map((event, index) => (
            <div key={index}>
              <b>{event.type}</b>:{" "}
              {event.type === "token"
                ? event.data.token
                : JSON.stringify(event.data)}
            </div>
          ))}
        </div>
      </Card>

      {/* APPROVAL */}

      {jobId && (
        <Card className="my-3" body>
          <h6>Approval</h6>

          <Button
            variant="success"
            className="me-2"
            onClick={() =>
              approval.mutate(
                {
                  decision: "approve",
                  outcome: "approved",
                  rationale: "Reviewed via UI",
                },
                {
                  onSuccess: () => refetchTrace(),
                },
              )
            }
          >
            Approve
          </Button>

          <Button
            variant="danger"
            onClick={() =>
              approval.mutate(
                {
                  decision: "reject",
                  rationale: "Reviewed via UI",
                },
                {
                  onSuccess: () => refetchTrace(),
                },
              )
            }
          >
            Reject
          </Button>
        </Card>
      )}

      {/* TRACE */}

      {jobId && (
        <Card className="my-3" body>
          <h6>
            Trace{" "}
            <Button
              size="sm"
              variant="outline-secondary"
              onClick={() => refetchTrace()}
            >
              Refresh
            </Button>
          </h6>

          {trace && (
            <Table size="sm" bordered>
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Kind</th>
                  <th>Detail</th>
                </tr>
              </thead>

              <tbody>
                {trace.map((item, index) => (
                  <tr key={index}>
                    <td>{item.timestamp}</td>

                    <td>{item.kind}</td>

                    <td>
                      <pre
                        className="mb-0"
                        style={{
                          fontSize: "0.75rem",
                        }}
                      >
                        {JSON.stringify(item.detail)}
                      </pre>
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>
          )}
        </Card>
      )}
    </Container>
  );
}
